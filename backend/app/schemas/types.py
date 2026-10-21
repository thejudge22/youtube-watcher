"""
Shared field types for API schemas.

SQLite stores datetimes without a timezone; every stored value is UTC. UTCDateTime
attaches UTC on the way out so clients get e.g. "2026-01-01T10:00:00Z" instead of
a naive string that browsers would read as local time.
"""
from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def ensure_utc(value: datetime) -> datetime:
    """Treat naive datetimes as UTC; convert aware ones to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


UTCDateTime = Annotated[datetime, AfterValidator(ensure_utc)]
