"""SQLModel tables."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Vehicle(SQLModel, table=True):
    """A vehicle observation (simulated / SUMO / YOLO-derived)."""
    id: int | None = Field(default=None, primary_key=True)
    vehicle_id: str = Field(index=True)
    vehicle_type: str  # car | bus | motorcycle | truck | ambulance
    junction_id: str | None = None
    edge: str | None = None
    x: float = 0.0
    y: float = 0.0
    speed_kmh: float = 0.0
    waiting_s: float = 0.0
    source: str = "simulated"  # simulated | sumo | yolo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


