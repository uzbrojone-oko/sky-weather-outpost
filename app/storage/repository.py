import json
import sqlite3
from pathlib import Path

from app.config.models import DeviceConfig, NodeConfig
from app.normalizers.rtl433 import NormalizedFrame


def store_frame(
    database_path: Path,
    frame: NormalizedFrame,
    *,
    site_id: str,
    node: NodeConfig,
    device: DeviceConfig,
) -> None:
    if device.key != frame.device_key:
        raise ValueError(
            f"Device {device.key!r} does not match frame {frame.device_key!r}"
        )

    received_at = frame.received_at.isoformat()
    measured_at = (
        frame.measured_at.isoformat() if frame.measured_at is not None else None
    )
    raw_json = json.dumps(frame.raw, separators=(",", ":"), sort_keys=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            INSERT INTO nodes (node_id, site_id, role)
            VALUES (?, ?, ?)
            ON CONFLICT (node_id) DO UPDATE SET
                site_id = excluded.site_id,
                role = excluded.role
            """,
            (node.id, site_id, node.role),
        )
        connection.execute(
            """
            INSERT INTO devices (device_key, node_id, name, type, public)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (device_key) DO UPDATE SET
                node_id = excluded.node_id,
                name = excluded.name,
                type = excluded.type,
                public = excluded.public
            """,
            (device.key, node.id, device.name, device.type, device.public),
        )
        cursor = connection.execute(
            """
            INSERT INTO raw_events (source, device_key, received_at, raw_json)
            VALUES (?, ?, ?, ?)
            """,
            ("rtl433", frame.device_key, received_at, raw_json),
        )
        raw_event_id = cursor.lastrowid

        connection.executemany(
            """
            INSERT INTO measurements (
                device_key,
                metric,
                value,
                unit,
                measured_at,
                received_at,
                raw_event_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    frame.device_key,
                    measurement.metric,
                    measurement.value,
                    measurement.unit,
                    measured_at,
                    received_at,
                    raw_event_id,
                )
                for measurement in frame.measurements
            ],
        )


def get_latest_reading(
    database_path: Path,
    device_key: str,
) -> dict[str, object] | None:
    with sqlite3.connect(database_path) as connection:
        event = connection.execute(
            """
            SELECT raw_event_id
            FROM measurements
            WHERE device_key = ?
            ORDER BY COALESCE(measured_at, received_at) DESC, measurement_id DESC
            LIMIT 1
            """,
            (device_key,),
        ).fetchone()

        if event is None:
            return None

        rows = connection.execute(
            """
            SELECT metric, value, unit, measured_at, received_at
            FROM measurements
            WHERE raw_event_id = ?
            ORDER BY measurement_id
            """,
            (event[0],),
        ).fetchall()

    if not rows:
        return None

    return {
        "device_key": device_key,
        "measured_at": rows[0][3],
        "received_at": rows[0][4],
        "measurements": {
            row[0]: {"value": row[1], "unit": row[2]}
            for row in rows
        },
    }
