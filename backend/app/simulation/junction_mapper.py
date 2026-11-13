"""Junction and lane topology mapping between SMARTFLOW app labels and SUMO IDs.

Maps:
- App IDs: J1 (Rasulgarh), J2 (Vani Vihar), J3 (Master Canteen), J4 (Khandagiri)
- Actual SUMO Junction / TLS IDs: A0, A1, B0, B1
- Approaches (N, S, E, W) to incoming edges and lanes
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
MAPPING_FILE = ROOT_DIR / "simulation" / "sumo" / "network" / "junction_mapping.json"

# In our generated 2x2 grid:
# A0=(150, 150) -> J1 (Rasulgarh)
# A1=(150, 450) -> J2 (Vani Vihar)
# B0=(450, 150) -> J3 (Master Canteen)
# B1=(450, 450) -> J4 (Khandagiri)
DEFAULT_APP_TO_SUMO = {
    "J1": "A0",
    "J2": "A1",
    "J3": "B0",
    "J4": "B1",
}

DEFAULT_SUMO_TO_APP = {v: k for k, v in DEFAULT_APP_TO_SUMO.items()}

# Approach incoming edge mapping
# For A0 (x=150, y=150):
# N comes from A1 (150, 450) -> edge A1A0
# S comes from bottom0 (150, 0) -> edge bottom0A0
# E comes from B0 (450, 150) -> edge B0A0
# W comes from left0 (0, 150) -> edge left0A0
INCOMING_APPROACH_EDGES: dict[str, dict[str, str]] = {
    "J1": {"N": "A1A0", "S": "bottom0A0", "E": "B0A0", "W": "left0A0"},
    "J2": {"N": "top0A1", "S": "A0A1", "E": "B1A1", "W": "left1A1"},
    "J3": {"N": "B1B0", "S": "bottom1B0", "E": "right0B0", "W": "A0B0"},
    "J4": {"N": "top1B1", "S": "B0B1", "E": "right1B1", "W": "A1B1"},
}

JUNCTION_NAMES: dict[str, str] = {
    "J1": "Rasulgarh",
    "J2": "Vani Vihar",
    "J3": "Master Canteen",
    "J4": "Khandagiri",
}

JUNCTION_POSITIONS: dict[str, tuple[float, float]] = {
    "J1": (150.0, 150.0),
    "J2": (150.0, 450.0),
    "J3": (450.0, 150.0),
    "J4": (450.0, 450.0),
}


class JunctionMapper:
    """Provides bi-directional resolution between application IDs and SUMO network IDs."""

    def __init__(self, mapping_path: Path | None = None) -> None:
        self.mapping_path = mapping_path or MAPPING_FILE
        self.app_to_sumo: dict[str, str] = dict(DEFAULT_APP_TO_SUMO)
        self.sumo_to_app: dict[str, str] = dict(DEFAULT_SUMO_TO_APP)
        self.approach_edges: dict[str, dict[str, str]] = dict(INCOMING_APPROACH_EDGES)
        self._load_mapping()

    def _load_mapping(self) -> None:
        if self.mapping_path.exists():
            try:
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "sumo_to_app" in data:
                        self.sumo_to_app = data["sumo_to_app"]
                        self.app_to_sumo = {v: k for k, v in self.sumo_to_app.items()}
            except Exception:
                pass

    def to_sumo_id(self, app_id: str) -> str:
        return self.app_to_sumo.get(app_id, app_id)

    def to_app_id(self, sumo_id: str) -> str:
        return self.sumo_to_app.get(sumo_id, sumo_id)

    def get_incoming_edge(self, app_id: str, approach: str) -> str:
        return self.approach_edges.get(app_id, {}).get(approach, "")

    def get_junction_name(self, app_id: str) -> str:
        return JUNCTION_NAMES.get(app_id, app_id)

    def get_position(self, app_id: str) -> tuple[float, float]:
        return JUNCTION_POSITIONS.get(app_id, (0.0, 0.0))
