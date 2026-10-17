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
