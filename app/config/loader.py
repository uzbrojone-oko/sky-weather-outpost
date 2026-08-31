from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.config.models import OutpostConfig


class ConfigError(ValueError):
    """Raised when an Outpost configuration cannot be loaded or validated."""


def load_config(path: str | Path) -> OutpostConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"Configuration root must be a mapping: {config_path}")

    try:
        return OutpostConfig.model_validate(raw)
    except ValidationError as exc:
        errors = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            errors.append(f"{location}: {error['msg']}")
        raise ConfigError("Configuration validation failed: " + "; ".join(errors)) from exc
