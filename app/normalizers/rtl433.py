"""Normalizer for rtl_433 JSON frames.

This module knows the rtl_433 vocabulary (field names, units, time format) and
nothing else. It does not know which devices are declared in the site config,
does not touch the database and does not log. Those are responsibilities of the
layers above it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SOURCE = "rtl433"


class FrameError(ValueError):
    """Raised when an rtl_433 line or frame cannot be interpreted."""


@dataclass(frozen=True)
class MeasurementDraft:
    """A normalized value, not yet tied to storage."""

    metric: str
    value: float
    unit: str


@dataclass(frozen=True)
class NormalizedFrame:
    """Generic result of normalizing one rtl_433 frame."""

    device_key: str
    measured_at: datetime | None  # UTC, or None when the frame carries no time
    received_at: datetime  # UTC
    measurements: tuple[MeasurementDraft, ...]
    raw: dict[str, Any] = field(compare=False)


def parse_line(line: str) -> dict[str, Any]:
    """Parse one JSONL line into a dict."""
    text = line.strip()
    if not text:
        raise FrameError("Empty line")
    try:
        frame = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FrameError(f"Invalid JSON: {exc}") from exc
    if not isinstance(frame, dict):
        raise FrameError("Frame must be a JSON object")
    return frame


def build_device_key(frame: dict[str, Any]) -> str:
    """Build `rtl433:model:channel:id`. A missing channel is an empty segment."""
    model = frame.get("model")
    device_id = frame.get("id")
    if model is None or device_id is None:
        raise FrameError("Frame has no model or id")
    channel = frame.get("channel", "")
    return f"{SOURCE}:{model}:{channel}:{device_id}"


def normalize(frame: dict[str, Any], site_timezone: str, received_at: datetime) -> NormalizedFrame:
    """Normalize one parsed frame.

    `site_timezone` is used to interpret the timezone-less source time.
    `received_at` must be timezone-aware; it is stored as UTC.
    """
    if received_at.tzinfo is None:
        raise ValueError("received_at must be timezone-aware")

    return NormalizedFrame(
        device_key=build_device_key(frame),
        measured_at=_parse_source_time(frame.get("time"), site_timezone),
        received_at=received_at.astimezone(UTC),
        measurements=_extract_measurements(frame),
        raw=frame,
    )


@lru_cache(maxsize=8)
def _zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {name}") from exc


def _parse_source_time(value: Any, site_timezone: str) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise FrameError(f"Unrecognized time format: {value!r}") from exc
    if parsed.tzinfo is not None:
        return parsed.astimezone(UTC)
    return parsed.replace(tzinfo=_zone(site_timezone)).astimezone(UTC)


def _number(frame: dict[str, Any], key: str) -> float | None:
    value = frame.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise FrameError(f"Field {key!r} is not a number: {value!r}")
    return float(value)


def _extract_measurements(frame: dict[str, Any]) -> tuple[MeasurementDraft, ...]:
    drafts: list[MeasurementDraft] = []

    temperature_c = _number(frame, "temperature_C")
    if temperature_c is None:
        temperature_f = _number(frame, "temperature_F")
        if temperature_f is not None:
            temperature_c = round((temperature_f - 32) * 5 / 9, 3)
    if temperature_c is not None:
        drafts.append(MeasurementDraft("temperature", temperature_c, "C"))

    humidity = _number(frame, "humidity")
    if humidity is not None:
        drafts.append(MeasurementDraft("humidity", humidity, "%"))

    battery_ok = _number(frame, "battery_ok")
    if battery_ok is not None:
        drafts.append(MeasurementDraft("battery_ok", battery_ok, "bool"))

    return tuple(drafts)
