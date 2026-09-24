from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.normalizers.rtl433 import (
    FrameError,
    MeasurementDraft,
    build_device_key,
    normalize,
    parse_line,
)

FIXTURE = Path(__file__).parent / "fixtures" / "rtl433-sample.jsonl"
TIMEZONE = "Europe/Warsaw"
RECEIVED_AT = datetime(2026, 9, 24, 19, 1, 36, tzinfo=UTC)


def fixture_lines() -> list[str]:
    return FIXTURE.read_text(encoding="utf-8").splitlines()


def measurements_by_metric(line: str) -> dict[str, MeasurementDraft]:
    result = normalize(parse_line(line), TIMEZONE, RECEIVED_AT)
    return {m.metric: m for m in result.measurements}


def test_known_sensor_frame_is_normalized():
    result = normalize(parse_line(fixture_lines()[1]), TIMEZONE, RECEIVED_AT)

    assert result.device_key == "rtl433:inFactory-TH:1:166"
    assert result.measured_at == datetime(2026, 9, 24, 19, 1, 35, tzinfo=UTC)
    assert result.received_at == RECEIVED_AT
    assert result.measurements == (
        MeasurementDraft("temperature", 11.611, "C"),
        MeasurementDraft("humidity", 82.0, "%"),
        MeasurementDraft("battery_ok", 1.0, "bool"),
    )


def test_device_key_without_channel_has_empty_segment():
    frame = parse_line(fixture_lines()[0])

    assert build_device_key(frame) == "rtl433:Toyota::00000001"


def test_unknown_metrics_are_left_in_raw_not_normalized():
    result = normalize(parse_line(fixture_lines()[0]), TIMEZONE, RECEIVED_AT)

    assert [m.metric for m in result.measurements] == ["temperature"]
    assert result.raw["pressure_kPa"] == 208.566


@pytest.mark.parametrize("line", ["", "   ", "not json", "[1, 2, 3]", '{"model": "x"'])
def test_unparseable_line_raises_frame_error(line: str):
    with pytest.raises(FrameError):
        parse_line(line)


def test_frame_without_model_or_id_is_rejected():
    with pytest.raises(FrameError, match="model or id"):
        normalize({"temperature_C": 20.0}, TIMEZONE, RECEIVED_AT)


def test_fahrenheit_is_converted_to_celsius():
    frame = {"model": "X", "id": 1, "temperature_F": 68.0}

    result = normalize(frame, TIMEZONE, RECEIVED_AT)

    assert result.measurements == (MeasurementDraft("temperature", 20.0, "C"),)


def test_implausible_reading_passes_through_unjudged():
    # Quality judgement belongs to a later layer, not to the normalizer.
    metrics = measurements_by_metric(fixture_lines()[10])

    assert metrics["temperature"].value == -35.556


def test_low_battery_is_a_measurement():
    metrics = measurements_by_metric(fixture_lines()[10])

    assert metrics["battery_ok"] == MeasurementDraft("battery_ok", 0.0, "bool")


def test_missing_time_gives_none():
    result = normalize({"model": "X", "id": 1, "humidity": 50}, TIMEZONE, RECEIVED_AT)

    assert result.measured_at is None


def test_bad_time_format_is_rejected():
    frame = {"model": "X", "id": 1, "time": "yesterday"}

    with pytest.raises(FrameError, match="time format"):
        normalize(frame, TIMEZONE, RECEIVED_AT)


def test_time_with_explicit_offset_ignores_site_timezone():
    frame = {"model": "X", "id": 1, "time": "2026-09-24T19:01:35+00:00"}

    result = normalize(frame, TIMEZONE, RECEIVED_AT)

    assert result.measured_at == datetime(2026, 9, 24, 19, 1, 35, tzinfo=UTC)


def test_non_numeric_value_is_rejected():
    frame = {"model": "X", "id": 1, "humidity": "wet"}

    with pytest.raises(FrameError, match="humidity"):
        normalize(frame, TIMEZONE, RECEIVED_AT)


def test_naive_received_at_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        normalize({"model": "X", "id": 1}, TIMEZONE, datetime(2026, 9, 24, 19, 0, 0))  # noqa: DTZ001


def test_unknown_timezone_is_rejected():
    frame = {"model": "X", "id": 1, "time": "2026-09-24 21:01:35"}

    with pytest.raises(ValueError, match="Unknown timezone"):
        normalize(frame, "Mars/Olympus", RECEIVED_AT)


def test_every_fixture_line_normalizes():
    lines = fixture_lines()

    results = [normalize(parse_line(line), TIMEZONE, RECEIVED_AT) for line in lines]

    assert len(results) == 14
    assert all(r.measured_at is not None for r in results)
