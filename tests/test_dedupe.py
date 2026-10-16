import importlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.config.loader import load_config
from app.core.devices import DeviceRegistry
from app.normalizers.rtl433 import normalize, parse_line

TIMEZONE = "Europe/Warsaw"
RECEIVED_AT = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)


def make_deduplicator(window_seconds=5):
    try:
        module = importlib.import_module("app.core.dedupe")
    except ModuleNotFoundError as exc:
        if exc.name != "app.core.dedupe":
            raise
        pytest.fail("Deduplicator is not implemented yet")

    return module.Deduplicator(window_seconds=window_seconds)


def make_frame(time, temperature=11.6, rssi=-20):
    return normalize(
        {
            "time": time,
            "model": "inFactory-TH",
            "id": 166,
            "channel": 1,
            "temperature_C": temperature,
            "humidity": 82,
            "battery_ok": 1,
            "rssi": rssi,
        },
        TIMEZONE,
        RECEIVED_AT,
    )


def test_same_reading_with_different_raw_noise_is_duplicate():
    deduplicator = make_deduplicator()

    first = make_frame("2026-09-24T19:01:35+00:00", rssi=-20)
    second = make_frame("2026-09-24T19:01:37+00:00", rssi=-55)

    assert deduplicator.is_duplicate(first) is False
    assert deduplicator.is_duplicate(second) is True


def test_different_reading_within_window_is_not_duplicate():
    deduplicator = make_deduplicator()

    first = make_frame("2026-09-24T19:01:35+00:00", temperature=11.6)
    second = make_frame("2026-09-24T19:01:37+00:00", temperature=11.7)

    assert deduplicator.is_duplicate(first) is False
    assert deduplicator.is_duplicate(second) is False


def test_city_lab_fixture_reduces_to_three_readings_and_nine_metrics():
    config = load_config(Path("config/examples/city-lab.yaml"))
    registry = DeviceRegistry(config.devices)
    deduplicator = make_deduplicator()
    fixture = Path("tests/fixtures/rtl433-sample.jsonl")

    accepted = []
    for line in fixture.read_text(encoding="utf-8").splitlines():
        frame = normalize(parse_line(line), TIMEZONE, RECEIVED_AT)
        if registry.get(frame.device_key) and not deduplicator.is_duplicate(frame):
            accepted.append(frame)

    assert len(accepted) == 3
    assert sum(len(frame.measurements) for frame in accepted) == 9
