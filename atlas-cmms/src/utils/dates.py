"""Date serialization and parsing utilities for ISO-8601 UTC milliseconds and Jackson timestamps."""

from datetime import datetime, timezone
from typing import Any


def format_iso_utc_ms(dt: datetime) -> str:
    """Serialize datetime to ISO-8601 UTC millisecond string: `2026-10-18T12:34:56.789+00:00`."""
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)
    ms = dt_utc.microsecond // 1000
    return f"{dt_utc.strftime('%Y-%m-%dT%H:%M:%S')}.{ms:03d}+00:00"


def parse_iso_datetime(val: Any) -> datetime:
    """Parse ISO-8601 string, numeric timestamp (ms or seconds), or datetime into UTC datetime."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)

    if isinstance(val, (int, float)):
        # Timestamps > 1e11 are epoch milliseconds (e.g. 1700000000000)
        ts = val / 1000.0 if val > 1e11 else float(val)
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if isinstance(val, str):
        cleaned = val.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    raise ValueError(f"Cannot parse datetime from {val!r}")


def to_epoch_ms(dt: datetime) -> int:
    """Convert datetime to milliseconds since Unix epoch."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def from_epoch_ms(ms: int | float) -> datetime:
    """Convert milliseconds since Unix epoch to UTC datetime."""
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)


serialize_datetime = format_iso_utc_ms
to_iso_utc = format_iso_utc_ms
parse_datetime = parse_iso_datetime
