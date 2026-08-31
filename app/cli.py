from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from app.config.loader import ConfigError, load_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="outpost")
    commands = parser.add_subparsers(dest="command", required=True)

    config_parser = commands.add_parser("config", help="Configuration commands")
    config_commands = config_parser.add_subparsers(dest="config_command", required=True)

    validate_parser = config_commands.add_parser("validate", help="Validate a YAML config")
    validate_parser.add_argument("path")

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

    return 2
