import sqlite3
from contextlib import closing
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

CURRENT_SCHEMA_VERSION = max(version for version, _ in _MIGRATIONS)


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



def _copy_verified_database(
    source_path: Path, destination_path: Path, *, operation: str
) -> None:
    """Copy an initialized Outpost database and verify it without overwriting."""
    source_path = Path(source_path)
    destination_path = Path(destination_path)

    if not source_path.is_file():
        raise FileNotFoundError(f"Database does not exist: {source_path}")
    if source_path.resolve() == destination_path.resolve():
        raise ValueError(
            f"{operation} destination must differ from the source database"
        )

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with destination_path.open("xb"):
        pass

    try:
        with closing(
            sqlite3.connect(
                source_path.resolve().as_uri() + "?mode=ro",
                uri=True,
            )
        ) as source_connection:
            schema = source_connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'schema_migrations'"
            ).fetchone()
            if schema is None:
                raise ValueError(
                    f"Not an initialized Outpost database: {source_path}"
                )
            with closing(sqlite3.connect(destination_path)) as destination_connection:
                source_connection.backup(destination_connection)

        with closing(
            sqlite3.connect(
                destination_path.resolve().as_uri() + "?mode=ro",
                uri=True,
            )
        ) as verification_connection:
            integrity = verification_connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()
            if integrity is None or integrity[0] != "ok":
                result = integrity[0] if integrity else "no result"
                raise sqlite3.DatabaseError(
                    f"{operation} integrity check failed: {result}"
                )
            schema = verification_connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'schema_migrations'"
            ).fetchone()
            if schema is None:
                raise sqlite3.DatabaseError(
                    "Backup is missing the schema_migrations table"
                )
    except BaseException:
        destination_path.unlink(missing_ok=True)
        raise


def backup_database(source_path: Path, destination_path: Path) -> None:
    """Create and verify a SQLite-safe backup without overwriting an existing file."""
    _copy_verified_database(source_path, destination_path, operation="Backup")


def restore_database(backup_path: Path, destination_path: Path) -> None:
    """Restore a verified backup to a new SQLite file without overwriting it."""
    _copy_verified_database(backup_path, destination_path, operation="Restore")
