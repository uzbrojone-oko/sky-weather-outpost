from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from app.config.loader import ConfigError, load_config
from app.ingest.replay import replay_jsonl
from app.ingest.rtl433 import Rtl433FrameProcessor
from app.storage.database import initialize_database
from app.storage.repository import store_frame


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

    rtl433_parser = commands.add_parser("rtl433", help="RTL-433 commands")
    rtl433_commands = rtl433_parser.add_subparsers(
        dest="rtl433_command", required=True
    )
    replay_parser = rtl433_commands.add_parser(
        "replay", help="Replay frames from a JSONL file"
    )
    replay_parser.add_argument("--config", required=True)
    replay_parser.add_argument("--input", required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

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
            config = load_config(args.config)
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

    return 2
