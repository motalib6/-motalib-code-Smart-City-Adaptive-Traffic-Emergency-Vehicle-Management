"""Shared Pydantic request/response schemas (typed, /api versioned)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool


class SimulationStartRequest(BaseModel):
    scenario: str = "normal"
    engine: str = "simulated"  # simulated | sumo


class ScenarioRequest(BaseModel):
    scenario: str


class TrafficInjectRequest(BaseModel):
    junction_id: str
    approach: str = Field(pattern="^(N|S|E|W)$")
    vehicle_count: int = Field(ge=0)
    queue_length: int = Field(ge=0, default=0)
    avg_wait_s: float = Field(ge=0, default=0.0)
    source: str = "manual"


class EmergencyCreateRequest(BaseModel):
    ambulance_id: str = "AMB-01"
    current_junction: str
    destination_junction: str
    route: list[str] = []
    speed_kmh: float = 40.0


class EmergencyLocationRequest(BaseModel):
    junction_id: str | None = None
    x: float | None = None
    y: float | None = None
    speed_kmh: float | None = None
    progress: float | None = None


class AdminSettingsRequest(BaseModel):
    green_min_s: int | None = Field(default=None, ge=5, le=30)
    green_max_s: int | None = Field(default=None, ge=20, le=120)
    yellow_s: int | None = Field(default=None, ge=2, le=6)
    all_red_s: int | None = Field(default=None, ge=1, le=5)
    demand_k: float | None = Field(default=None, ge=0.1, le=3.0)
    w_queue: float | None = None
    w_count: float | None = None
    w_wait: float | None = None
    scenario: str | None = None


class EventOut(BaseModel):
    id: int
    type: str
    junction_id: str | None
    message: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
