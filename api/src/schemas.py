"""Shared types and base schemas.

``UtcDatetime`` is an ``Annotated`` datetime that serialises to a UTC ISO-8601
string with a ``Z`` suffix when used in Pydantic JSON responses.  This fixes
the 3-hour offset that occurs when JavaScript's ``new Date()`` receives a
naive datetime string (no ``Z``) and interprets it as local time instead of UTC.

Usage in schemas::

    from src.schemas import UtcDatetime

    class MyOut(BaseModel):
        created_at: UtcDatetime
        model_config = {"from_attributes": True}
"""
from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def _to_utc_str(v: datetime) -> str:
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    return v.isoformat().replace("+00:00", "Z")


# Use this instead of ``datetime`` for any timestamp field in a response schema.
UtcDatetime = Annotated[
    datetime,
    PlainSerializer(_to_utc_str, return_type=str, when_used="json"),
]
