"""SQLModel tables."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SimulationRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mode: str  # fixed | adaptive
    scenario: str = "normal"
    seed: int = 42
    duration_s: int = 0
    mean_wait_s: float | None = None
    mean_queue: float | None = None
    throughput: int | None = None
    max_queue: int | None = None
    emergency_travel_s: float | None = None
    status: str = "completed"  # completed | planned
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
