"""SQLModel tables."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Junction(SQLModel, table=True):
    id: str = Field(primary_key=True)  # J1..J4
    name: str
    x: float = 0.0
    y: float = 0.0
    lanes: int = 4
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


