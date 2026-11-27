from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config.models import OutpostConfig
from app.storage.database import CURRENT_SCHEMA_VERSION
from app.storage.repository import get_latest_reading

SENSOR_STALE_AFTER_SECONDS = 15 * 60


@dataclass(frozen=True)
class StatusReport:
    lines: tuple[str, ...]
    exit_code: int


def build_status_report(
    config: OutpostConfig,
    *,
    now: datetime | None = None,
) -> StatusReport:
    """Read local database, sensor and backup state without changing anything."""
    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    lines = [
        "Sky Weather Outpost — status",
        f"Lokalizacja: {config.site.name}",
        f"Węzeł: {config.node.name or config.node.id}",
    ]
    has_warning = False
    database_path = Path(config.storage.sqlite_path)

    try:
        schema_version = _check_database(database_path)
    except (OSError, sqlite3.Error, ValueError) as exc:
        lines.append(f"Baza: BŁĄD · {exc}")
        has_warning = True
    else:
        lines.append(
            "Baza: OK · integralność OK · "
            f"migracja {schema_version}/{CURRENT_SCHEMA_VERSION}"
        )
        for device in config.devices:
            if device.type != "weather_sensor":
                continue
            try:
                reading = get_latest_reading(database_path, device.key)
            except (OSError, sqlite3.Error) as exc:
                lines.append(f"Czujnik {device.name}: BŁĄD · {exc}")
                has_warning = True
                continue

            if reading is None:
                lines.append(f"Czujnik {device.name}: BRAK POMIARÓW")
                has_warning = True
                continue

            received_at = _parse_timestamp(reading["received_at"])
            age_seconds = max(
                0, int((current_time.astimezone(UTC) - received_at).total_seconds())
            )
            freshness = "OK"
            if age_seconds > SENSOR_STALE_AFTER_SECONDS:
                freshness = "NIEAKTUALNY"
                has_warning = True

            battery = reading["measurements"].get("battery_ok")
            if battery is None:
                battery_text = "bateria nieznana"
            elif float(battery["value"]) >= 1:
                battery_text = "bateria OK"
            else:
                battery_text = "niska bateria"
                has_warning = True

            local_time = received_at.astimezone(ZoneInfo(config.site.timezone))
            lines.append(
                f"Czujnik {device.name}: {freshness} · sygnał "
                f"{local_time:%d.%m %H:%M} ({_format_age(age_seconds)}) · "
                f"{battery_text}"
            )

    try:
        backup = _latest_backup(database_path)
    except OSError as exc:
        lines.append(f"Backup: BŁĄD · {exc}")
        has_warning = True
    else:
        if backup is None:
            lines.append("Backup: BRAK")
            has_warning = True
        else:
            backup_path, modified_at = backup
            backup_age = max(
                0,
                int(
                    (
                        current_time.astimezone(UTC)
                        - datetime.fromtimestamp(modified_at, UTC)
                    ).total_seconds()
                ),
            )
            local_backup_time = datetime.fromtimestamp(
                modified_at, ZoneInfo(config.site.timezone)
            )
            lines.append(
                f"Backup: {backup_path.name} · "
                f"{local_backup_time:%d.%m.%Y %H:%M} "
                f"({_format_age(backup_age)})"
            )

    return StatusReport(tuple(lines), 1 if has_warning else 0)


def _check_database(database_path: Path) -> int:
    if not database_path.is_file():
        raise FileNotFoundError(f"brak pliku {database_path}")

    uri = database_path.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            result = integrity[0] if integrity else "brak wyniku"
            raise sqlite3.DatabaseError(f"integralność: {result}")

        versions = {
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        }

    if not versions:
        raise sqlite3.DatabaseError("brak zastosowanych migracji")
    if max(versions) != CURRENT_SCHEMA_VERSION:
        raise sqlite3.DatabaseError(
            f"oczekiwano migracji {CURRENT_SCHEMA_VERSION}, "
            f"znaleziono {max(versions)}"
        )
    return max(versions)


def _latest_backup(database_path: Path) -> tuple[Path, float] | None:
    backup_directory = database_path.parent / "backups"
    if not backup_directory.is_dir():
        return None

    candidates = list(backup_directory.glob("*.sqlite"))
    if not candidates:
        return None

    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    return latest, latest.stat().st_mtime


def _parse_timestamp(value: object) -> datetime:
    timestamp = datetime.fromisoformat(str(value))
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def _format_age(seconds: int) -> str:
    if seconds < 60:
        return "mniej niż minutę temu"
    if seconds < 3600:
        return f"{seconds // 60} min temu"
    if seconds < 86400:
        return f"{seconds // 3600} godz. temu"
    return f"{seconds // 86400} dni temu"
