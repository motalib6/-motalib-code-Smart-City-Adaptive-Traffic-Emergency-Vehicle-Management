"""SQLModel tables."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: str = Field(index=True)  # e.g. EMERGENCY_REQUESTED, PHASE_CHANGED
    junction_id: str | None = None
    message: str = ""
    source: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


