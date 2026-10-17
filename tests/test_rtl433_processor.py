import json
from datetime import UTC, datetime
from pathlib import Path

from app.config.loader import load_config
from app.ingest.rtl433 import Rtl433FrameProcessor

TIMEZONE = "Europe/Warsaw"
RECEIVED_AT = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)


def make_processor():
    config = load_config(Path("config/examples/city-lab.yaml"))
    return Rtl433FrameProcessor(
        devices=config.devices,
        site_timezone=TIMEZONE,
    )


def test_city_lab_jsonl_replay_emits_three_readings_and_nine_metrics():
    processor = make_processor()
    fixture = Path("tests/fixtures/rtl433-sample.jsonl")

    accepted = []
    for line in fixture.read_text(encoding="utf-8").splitlines():
        frame = processor.process_line(line, RECEIVED_AT)
        if frame is not None:
            accepted.append(frame)

    assert len(accepted) == 3
    assert sum(len(frame.measurements) for frame in accepted) == 9


def test_duplicate_jsonl_line_is_dropped():
    processor = make_processor()
    line = Path("tests/fixtures/rtl433-sample.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()[1]

    first = processor.process_line(line, RECEIVED_AT)
    duplicate = processor.process_line(line, RECEIVED_AT)

    assert first is not None
    assert duplicate is None


def test_duplicate_jsonl_line_without_source_time_is_dropped():
    processor = make_processor()
    data = json.loads(
        Path("tests/fixtures/rtl433-sample.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[1]
    )
    data.pop("time", None)
    line = json.dumps(data)

    first = processor.process_line(line, RECEIVED_AT)
    duplicate = processor.process_line(line, RECEIVED_AT)

    assert first is not None
    assert duplicate is None


def test_jsonl_file_replay_emits_three_readings_and_nine_metrics():
    from app.ingest.replay import replay_jsonl

    frames = list(
        replay_jsonl(
            Path("tests/fixtures/rtl433-sample.jsonl"),
            make_processor(),
            RECEIVED_AT,
        )
    )

    assert len(frames) == 3
    assert sum(len(frame.measurements) for frame in frames) == 9
