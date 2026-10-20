import sqlite3
from pathlib import Path

from app.storage.database import initialize_database


def test_initialize_database_creates_initial_schema(tmp_path: Path):
    database_path = tmp_path / "outpost.sqlite"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        versions = connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()

    assert {
        "schema_migrations",
        "nodes",
        "devices",
        "raw_events",
        "measurements",
        "system_events",
    } <= tables
    assert versions == [(1,)]


def test_initialize_database_does_not_apply_migration_twice(tmp_path: Path):
    database_path = tmp_path / "outpost.sqlite"

    initialize_database(database_path)
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        versions = connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()

    assert versions == [(1,)]


def test_jsonl_replay_stores_raw_events_and_measurements(tmp_path: Path):
    from datetime import UTC, datetime

    from app.config.loader import load_config
    from app.ingest.replay import replay_jsonl
    from app.ingest.rtl433 import Rtl433FrameProcessor
    from app.storage.repository import get_latest_reading, store_frame

    config = load_config(Path("config/examples/city-lab.yaml"))
    processor = Rtl433FrameProcessor(config.devices, config.site.timezone)
    received_at = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    fixture = Path("tests/fixtures/rtl433-sample.jsonl")
    database_path = tmp_path / "outpost.sqlite"

    initialize_database(database_path)
    frames = list(replay_jsonl(fixture, processor, received_at))

    for frame in frames:
        device = next(item for item in config.devices if item.key == frame.device_key)
        store_frame(
            database_path,
            frame,
            site_id=config.site.id,
            node=config.node,
            device=device,
        )

    with sqlite3.connect(database_path) as connection:
        raw_event_count = connection.execute(
            "SELECT COUNT(*) FROM raw_events"
        ).fetchone()[0]
        measurement_count = connection.execute(
            "SELECT COUNT(*) FROM measurements"
        ).fetchone()[0]

    assert raw_event_count == 3
    assert measurement_count == 9

    latest = get_latest_reading(database_path, frames[-1].device_key)
    measured_at = (
        frames[-1].measured_at.isoformat()
        if frames[-1].measured_at is not None
        else None
    )
    assert latest == {
        "device_key": frames[-1].device_key,
        "measured_at": measured_at,
        "received_at": frames[-1].received_at.isoformat(),
        "measurements": {
            measurement.metric: {
                "value": measurement.value,
                "unit": measurement.unit,
            }
            for measurement in frames[-1].measurements
        },
    }


def test_get_latest_reading_uses_measurement_time_not_replay_receive_time(
    tmp_path: Path,
):
    from app.storage.repository import get_latest_reading

    database_path = tmp_path / "outpost.sqlite"
    device_key = "rtl433:inFactory-TH:1:166"
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO nodes (node_id, site_id, role) VALUES (?, ?, ?)",
            ("city-lab-core", "city-lab", "core"),
        )
        connection.execute(
            """
            INSERT INTO devices (device_key, node_id, name, type, public)
            VALUES (?, ?, ?, ?, ?)
            """,
            (device_key, "city-lab-core", "Weather sensor", "weather_sensor", 1),
        )

        events = [
            (
                "2026-10-19T14:48:32+00:00",
                "2026-10-19T14:48:31+00:00",
                10.444,
            ),
            (
                "2026-10-20T12:32:03+00:00",
                "2026-09-24T19:09:38+00:00",
                11.667,
            ),
        ]

        for received_at, measured_at, value in events:
            cursor = connection.execute(
                """
                INSERT INTO raw_events (source, device_key, received_at, raw_json)
                VALUES (?, ?, ?, ?)
                """,
                ("rtl433", device_key, received_at, "{}"),
            )
            connection.execute(
                """
                INSERT INTO measurements (
                    device_key, metric, value, unit, measured_at, received_at, raw_event_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device_key,
                    "temperature",
                    value,
                    "C",
                    measured_at,
                    received_at,
                    cursor.lastrowid,
                ),
            )

    reading = get_latest_reading(database_path, device_key)

    assert reading is not None
    assert reading["measured_at"] == "2026-10-19T14:48:31+00:00"
    assert reading["measurements"]["temperature"]["value"] == 10.444
