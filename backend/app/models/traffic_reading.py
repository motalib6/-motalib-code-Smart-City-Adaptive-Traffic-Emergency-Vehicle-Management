"""SQLModel tables."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class TrafficReading(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    junction_id: str = Field(index=True)
    approach: str  # N | S | E | W
    vehicle_count: int = 0
    queue_length: int = 0
    avg_wait_s: float = 0.0
    density_score: float = 0.0
    source: str = "simulated"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


