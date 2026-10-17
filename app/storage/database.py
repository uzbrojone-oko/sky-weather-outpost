import sqlite3
from pathlib import Path

_MIGRATIONS = (
    (
        1,
        (
            """
            CREATE TABLE nodes (
                node_id TEXT PRIMARY KEY,
                site_id TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE devices (
                device_key TEXT PRIMARY KEY,
                node_id TEXT NOT NULL REFERENCES nodes(node_id),
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                public INTEGER NOT NULL CHECK (public IN (0, 1))
            )
            """,
            """
            CREATE TABLE raw_events (
                raw_event_id INTEGER PRIMARY KEY,
                source TEXT NOT NULL,
                device_key TEXT,
                received_at TEXT NOT NULL,
                raw_json TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE measurements (
                measurement_id INTEGER PRIMARY KEY,
                device_key TEXT NOT NULL REFERENCES devices(device_key),
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                measured_at TEXT,
                received_at TEXT NOT NULL,
                raw_event_id INTEGER REFERENCES raw_events(raw_event_id)
            )
            """,
            """
            CREATE TABLE system_events (
                system_event_id INTEGER PRIMARY KEY,
                node_id TEXT REFERENCES nodes(node_id),
                level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ),
    ),
)


def initialize_database(path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        for version, statements in _MIGRATIONS:
            applied = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,),
            ).fetchone()
            if applied:
                continue

            connection.execute("BEGIN")
            try:
                for statement in statements:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (version,),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
