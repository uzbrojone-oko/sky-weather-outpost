from __future__ import annotations

import argparse
import csv
import io
import json
import sqlite3
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from app.api.server import create_api_server
from app.config.loader import ConfigError, load_config, resolve_config_path
from app.history import HISTORY_PERIODS, history_window
from app.ingest.replay import replay_jsonl
from app.ingest.rtl433 import Rtl433FrameProcessor
from app.storage.database import backup_database, initialize_database
from app.storage.repository import (
    get_latest_reading,
    get_reading_history,
    store_frame,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="outpost")
    commands = parser.add_subparsers(dest="command", required=True)

    config_parser = commands.add_parser("config", help="Configuration commands")
    config_commands = config_parser.add_subparsers(
        dest="config_command", required=True
    )
    validate_parser = config_commands.add_parser(
        "validate", help="Validate a YAML config"
    )
    validate_parser.add_argument("path")

    backup_parser = commands.add_parser(
        "backup", help="Create a verified SQLite database backup"
    )
    backup_parser.add_argument("--config")
    backup_parser.add_argument(
        "--output",
        help="Backup file path (default: a timestamped file beside the database)",
    )

    rtl433_parser = commands.add_parser("rtl433", help="RTL-433 commands")
    rtl433_commands = rtl433_parser.add_subparsers(
        dest="rtl433_command", required=True
    )
    replay_parser = rtl433_commands.add_parser(
        "replay", help="Replay frames from a JSONL file"
    )
    replay_parser.add_argument("--config")
    replay_parser.add_argument("--input", required=True)
    ingest_parser = rtl433_commands.add_parser(
        "ingest", help="Ingest live RTL-433 JSONL from stdin"
    )
    ingest_parser.add_argument("--config")

    api_parser = commands.add_parser("api", help="API commands")
    api_commands = api_parser.add_subparsers(
        dest="api_command", required=True
    )
    serve_parser = api_commands.add_parser("serve", help="Serve the API")
    serve_parser.add_argument("--config")
    serve_parser.add_argument("--host")

    weather_parser = commands.add_parser("weather", help="Weather commands")
    weather_commands = weather_parser.add_subparsers(
        dest="weather_command", required=True
    )
    current_parser = weather_commands.add_parser(
        "current", help="Show the latest weather reading"
    )
    current_source = current_parser.add_mutually_exclusive_group()
    current_source.add_argument("--config")
    current_source.add_argument("--url")

    history_parser = weather_commands.add_parser(
        "history", help="Show aggregated weather history"
    )
    history_parser.add_argument(
        "--period",
        choices=tuple(HISTORY_PERIODS),
        default=None,
    )
    history_parser.add_argument(
        "--from",
        dest="range_from",
        help="ISO-8601 start timestamp with timezone",
    )
    history_parser.add_argument(
        "--to",
        dest="range_to",
        help="ISO-8601 end timestamp with timezone",
    )
    history_parser.add_argument(
        "--bucket",
        choices=("15m", "1h", "6h", "1d"),
        help="Aggregation bucket for a custom date range",
    )
    history_parser.add_argument("--config")
    history_parser.add_argument(
        "--format",
        choices=("table", "csv"),
        default="table",
        help="Output format (default: table)",
    )
    history_parser.add_argument(
        "--output",
        help="Write the result to a file instead of stdout",
    )

    return parser



def _format_number(value: object, *, compact: bool = False) -> str:
    number = float(value)
    if compact and number.is_integer():
        return str(int(number))
    return f"{number:.1f}".replace(".", ",")


def _format_current_weather(
    site_name: str,
    timezone: str,
    readings: list[dict],
) -> str:
    if not readings:
        return "Brak zapisanych pomiarów.\n"

    lines = []
    for reading in readings:
        measurements = reading["measurements"]
        timestamp = reading.get("measured_at") or reading["received_at"]
        local_time = datetime.fromisoformat(str(timestamp)).astimezone(
            ZoneInfo(timezone)
        )

        lines.extend((site_name, f"Pomiar: {local_time:%d.%m.%Y, %H:%M}", ""))

        temperature = measurements.get("temperature")
        if temperature is not None:
            unit = "°C" if temperature.get("unit") == "C" else temperature["unit"]
            lines.append(
                f"Temperatura: {_format_number(temperature['value'])} {unit}"
            )

        humidity = measurements.get("humidity")
        if humidity is not None:
            lines.append(
                f"Wilgotność: {_format_number(humidity['value'], compact=True)}%"
            )

        battery = measurements.get("battery_ok")
        if battery is not None:
            status = "OK" if float(battery["value"]) >= 1 else "niska"
            lines.append(f"Bateria: {status}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


_HISTORY_LABELS = {
    "day": "ostatnie 24 godziny",
    "week": "ostatnie 7 dni",
    "month": "ostatnie 30 dni",
    "year": "ostatnie 365 dni",
}

_HISTORY_BUCKETS = {
    "15m": 15 * 60,
    "1h": 60 * 60,
    "6h": 6 * 60 * 60,
    "1d": 24 * 60 * 60,
}


def _parse_history_timestamp(value: str, option: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an ISO-8601 timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{option} must include a timezone offset, for example +01:00")
    return timestamp.astimezone(UTC)


def _format_history_number(value: object) -> str:
    return f"{float(value):.1f}".replace(".", ",")


def _format_history(
    site_name: str,
    timezone: str,
    period: str,
    devices: list[tuple[str, list[dict[str, object]]]],
    *,
    title: str | None = None,
) -> str:
    lines = [f"{site_name} — historia: {title or _HISTORY_LABELS[period]}"]
    rows: list[list[str]] = []
    for device_name, points in devices:
        for point in points:
            local_time = datetime.fromisoformat(str(point["at"])).astimezone(
                ZoneInfo(timezone)
            )
            measurements = point["measurements"]
            cells = [
                f"{local_time:%d.%m.%Y %H:%M}",
                device_name,
            ]
            for metric in ("temperature", "humidity"):
                value = measurements.get(metric)
                if value is None:
                    cells.append("—")
                    continue
                average = _format_history_number(value["average"])
                minimum = _format_history_number(value["min"])
                maximum = _format_history_number(value["max"])
                samples = int(value["samples"])
                unit = "°C" if metric == "temperature" else "%"
                cells.append(
                    f"{average} [{minimum}–{maximum}] {unit} (n={samples})"
                )
            rows.append(cells)

    if not rows:
        lines.append("Brak zapisanych pomiarów w wybranym zakresie.")
        return "\n".join(lines) + "\n"

    headers = ["Czas lokalny", "Czujnik", "Temperatura", "Wilgotność"]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    lines.append(
        "  ".join(
            header.ljust(widths[index])
            for index, header in enumerate(headers)
        )
    )
    lines.append("  ".join("─" * width for width in widths))
    lines.extend(
        "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        for row in rows
    )
    return "\n".join(lines) + "\n"


def _format_history_csv(
    devices: list[tuple[str, list[dict[str, object]]]],
) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "timestamp_utc",
            "sensor",
            "temperature_average_C",
            "temperature_min_C",
            "temperature_max_C",
            "temperature_samples",
            "humidity_average_percent",
            "humidity_min_percent",
            "humidity_max_percent",
            "humidity_samples",
        ]
    )
    for device_name, points in devices:
        for point in points:
            measurements = point["measurements"]
            temperature = measurements.get("temperature", {})
            humidity = measurements.get("humidity", {})
            writer.writerow(
                [
                    point["at"],
                    device_name,
                    temperature.get("average", ""),
                    temperature.get("min", ""),
                    temperature.get("max", ""),
                    temperature.get("samples", ""),
                    humidity.get("average", ""),
                    humidity.get("min", ""),
                    humidity.get("max", ""),
                    humidity.get("samples", ""),
                ]
            )
    return output.getvalue()


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "backup":
        try:
            config = load_config(resolve_config_path(args.config))
            database_path = Path(config.storage.sqlite_path)
            if args.output:
                backup_path = Path(args.output)
            else:
                backup_directory = database_path.parent / "backups"
                timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
                backup_path = backup_directory / (
                    f"{database_path.stem}-{timestamp}.sqlite"
                )
                suffix = 1
                while backup_path.exists():
                    backup_path = backup_directory / (
                        f"{database_path.stem}-{timestamp}-{suffix}.sqlite"
                    )
                    suffix += 1
            backup_database(database_path, backup_path)
        except (
            ConfigError,
            OSError,
            ValueError,
            sqlite3.Error,
        ) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        print(f"Backup created: {backup_path}")
        return 0

    if args.command == "config" and args.config_command == "validate":
        try:
            config = load_config(args.path)
        except ConfigError as exc:
            print(str(exc), file=sys.stderr)
            return 2

        print("Configuration valid")
        print(f"site: {config.site.id}")
        print(f"node: {config.node.id}")
        return 0

    if args.command == "rtl433" and args.rtl433_command == "replay":
        try:
            config = load_config(resolve_config_path(args.config))
            processor = Rtl433FrameProcessor(
                devices=config.devices,
                site_timezone=config.site.timezone,
            )
            frames = list(
                replay_jsonl(
                    Path(args.input),
                    processor,
                    datetime.now(UTC),
                )
            )

            database_path = Path(config.storage.sqlite_path)
            initialize_database(database_path)
            devices = {device.key: device for device in config.devices}
            for frame in frames:
                store_frame(
                    database_path,
                    frame,
                    site_id=config.site.id,
                    node=config.node,
                    device=devices[frame.device_key],
                )
        except (ConfigError, OSError, ValueError, sqlite3.Error) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        metric_count = sum(len(frame.measurements) for frame in frames)
        print("Replay complete")
        print(f"readings: {len(frames)}")
        print(f"metrics: {metric_count}")
        return 0

    if args.command == "rtl433" and args.rtl433_command == "ingest":
        try:
            config = load_config(resolve_config_path(args.config))
            processor = Rtl433FrameProcessor(
                devices=config.devices,
                site_timezone=config.site.timezone,
            )
            database_path = Path(config.storage.sqlite_path)
            initialize_database(database_path)
            devices = {device.key: device for device in config.devices}
            reading_count = 0
            metric_count = 0
            interrupted = False

            try:
                for line in sys.stdin:
                    if not line.strip():
                        continue

                    try:
                        frame = processor.process_line(line, datetime.now(UTC))
                    except ValueError as exc:
                        print(
                            f"discarded invalid RTL-433 frame: {exc}",
                            file=sys.stderr,
                            flush=True,
                        )
                        continue

                    if frame is None:
                        continue

                    store_frame(
                        database_path,
                        frame,
                        site_id=config.site.id,
                        node=config.node,
                        device=devices[frame.device_key],
                    )
                    print(
                        f"stored reading: device={frame.device_key} "
                        f"metrics={len(frame.measurements)} "
                        f"received_at={frame.received_at.isoformat()}",
                        file=sys.stderr,
                        flush=True,
                    )
                    reading_count += 1
                    metric_count += len(frame.measurements)
            except KeyboardInterrupt:
                interrupted = True
        except (ConfigError, OSError, ValueError, sqlite3.Error) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        message = "Ingest interrupted" if interrupted else "Ingest complete"
        print(message)
        print(f"readings: {reading_count}")
        print(f"metrics: {metric_count}")
        return 130 if interrupted else 0

    if args.command == "weather" and args.weather_command == "history":
        try:
            config = load_config(resolve_config_path(args.config))
            database_path = Path(config.storage.sqlite_path)
            initialize_database(database_path)
            has_range_start = args.range_from is not None
            has_range_end = args.range_to is not None
            if has_range_start != has_range_end:
                raise ValueError("--from and --to must be provided together")

            if has_range_start:
                if args.period is not None:
                    raise ValueError("--period cannot be combined with --from/--to")
                start_at = _parse_history_timestamp(args.range_from, "--from")
                end_at = _parse_history_timestamp(args.range_to, "--to")
                if end_at <= start_at:
                    raise ValueError("--to must be later than --from")
                bucket_label = args.bucket or "1h"
                bucket_seconds = _HISTORY_BUCKETS[bucket_label]
                history_period = "day"
                start_local = start_at.astimezone(ZoneInfo(config.site.timezone))
                end_local = end_at.astimezone(ZoneInfo(config.site.timezone))
                history_title = (
                    f"zakres {start_local:%d.%m.%Y %H:%M}–"
                    f"{end_local:%d.%m.%Y %H:%M} · kubełek {bucket_label}"
                )
            else:
                if args.bucket is not None:
                    raise ValueError("--bucket requires --from and --to")
                history_period = args.period or "day"
                start_at, end_at, bucket_seconds = history_window(history_period)
                history_title = None

            devices = []
            for device in config.devices:
                if device.type != "weather_sensor":
                    continue
                points = get_reading_history(
                    database_path,
                    device.key,
                    start_at=start_at,
                    end_at=end_at,
                    bucket_seconds=bucket_seconds,
                )
                if points:
                    devices.append((device.name, points))

            output = (
                _format_history_csv(devices)
                if args.format == "csv"
                else _format_history(
                    config.site.name,
                    config.site.timezone,
                    history_period,
                    devices,
                    title=history_title,
                )
            )
            if args.output:
                Path(args.output).write_text(output, encoding="utf-8")
                print(f"History written to {args.output}", file=sys.stderr)
            else:
                print(output, end="")
        except (
            ConfigError,
            OSError,
            ValueError,
            sqlite3.Error,
            KeyError,
            TypeError,
        ) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0

    if args.command == "weather" and args.weather_command == "current":
        try:
            if args.url is not None:
                with urlopen(args.url, timeout=2) as response:
                    payload = json.load(response)
                site_name = payload["site"]["name"]
                timezone = payload["site"]["timezone"]
                readings = [
                    device
                    for device in payload["devices"]
                    if device["type"] == "weather_sensor"
                ]
            else:
                config = load_config(resolve_config_path(args.config))
                database_path = Path(config.storage.sqlite_path)
                initialize_database(database_path)
                site_name = config.site.name
                timezone = config.site.timezone
                readings = []

                for device in config.devices:
                    if device.type != "weather_sensor":
                        continue
                    reading = get_latest_reading(database_path, device.key)
                    if reading is not None:
                        readings.append(reading)

            print(_format_current_weather(site_name, timezone, readings), end="")
        except (
            ConfigError,
            OSError,
            ValueError,
            sqlite3.Error,
            KeyError,
            TypeError,
        ) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        return 0

    if args.command == "api" and args.api_command == "serve":
        try:
            config = load_config(resolve_config_path(args.config))
            server = create_api_server(config, host=args.host)
        except (ConfigError, OSError, ValueError, sqlite3.Error) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        host, port = server.server_address[:2]
        print(f"API listening at http://{host}:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return 130
        finally:
            server.server_close()
        return 0

    return 2
