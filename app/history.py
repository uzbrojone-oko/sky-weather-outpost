from __future__ import annotations

from datetime import UTC, datetime, timedelta

HISTORY_PERIODS = {
    "day": (timedelta(days=1), 15 * 60),
    "week": (timedelta(days=7), 60 * 60),
    "month": (timedelta(days=30), 6 * 60 * 60),
    "year": (timedelta(days=365), 24 * 60 * 60),
}


def history_window(
    period: str,
    *,
    end_at: datetime | None = None,
) -> tuple[datetime, datetime, int]:
    """Return the UTC start, end and bucket size for a rolling history period."""
    if period not in HISTORY_PERIODS:
        raise ValueError(f"Unsupported history period: {period}")
    if end_at is None:
        end_at = datetime.now(UTC)
    elif end_at.tzinfo is None:
        raise ValueError("History end_at must be timezone-aware")

    end_utc = end_at.astimezone(UTC)
    duration, bucket_seconds = HISTORY_PERIODS[period]
    return end_utc - duration, end_utc, bucket_seconds
