"""SQLModel tables."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Emergency(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ambulance_id: str
    current_junction: str
    destination_junction: str
    route: str = ""  # comma-separated junction ids, e.g. J1,J2,J4
    status: str = "REQUESTED"  # REQUESTED|EN_ROUTE|PRIORITY_GRANTED|COMPLETED
    speed_kmh: float = 40.0
    progress: float = 0.0
    eta_s: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


