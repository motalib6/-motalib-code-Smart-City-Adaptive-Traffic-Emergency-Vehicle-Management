"""SQLModel tables."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SignalState(SQLModel, table=True):
    """Persisted signal-phase snapshot per junction."""
    id: int | None = Field(default=None, primary_key=True)
    junction_id: str = Field(index=True)
    phase: str  # GREEN_NS | YELLOW_NS | ALL_RED | GREEN_EW | YELLOW_EW
    green_duration_s: float = 30.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


