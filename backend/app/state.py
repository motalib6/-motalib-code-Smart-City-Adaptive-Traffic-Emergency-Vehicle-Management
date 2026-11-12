"""Shared runtime state (in-memory, single-process).

Holds the active simulation engine, live signal phases, admin settings and
vision state. Persistent facts live in SQLite; this is live/ephemeral state.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "green_min_s": settings.green_min_s,
    "green_max_s": settings.green_max_s,
    "yellow_s": settings.yellow_s,
    "all_red_s": settings.all_red_s,
    "demand_k": settings.demand_k,
    "w_queue": settings.w_queue,
    "w_count": settings.w_count,
    "w_wait": settings.w_wait,
    "scenario": "normal",
    "input_source": "simulated",  # "simulated" | "sumo" | "yolo"
}


class AppState:
    def __init__(self) -> None:
        self.engine = None  # SimulationEngine (set in main lifespan)
        self.engine_source: str = "simulated"
        self.running: bool = False
        self.tick: int = 0
        self.settings: dict[str, Any] = self._load_settings()
        self.vision: dict[str, Any] = {
            "status": "idle",  # idle | running | stopped | unavailable
            "source": None,
            "filename": None,
            "last_counts": {},
            "detector_available": False,
        }
        self.phases: dict[str, str] = {f"J{i}": "GREEN_NS" for i in range(1, 5)}
        self.phase_started_tick: dict[str, int] = {f"J{i}": 0 for i in range(1, 5)}
        self.emergency_active: dict[str, Any] | None = None

    def _load_settings(self) -> dict[str, Any]:
        if SETTINGS_FILE.exists():
            try:
                return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_FILE.read_text())}
            except Exception:
                pass
        return dict(DEFAULT_SETTINGS)

    def save_settings(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2))


STATE = AppState()
