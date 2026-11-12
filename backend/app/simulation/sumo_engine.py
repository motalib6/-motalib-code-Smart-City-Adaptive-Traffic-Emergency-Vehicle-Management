"""Real SUMO engine via TraCI.

Lazy-imports traci/sumolib (shipped with Eclipse SUMO). If SUMO is not
installed, `available` is False and start() raises RuntimeError with the
exact problem — the backend then uses SimulatedEngine and says so.
SUMO is NOT installed in this VM (``sumo``: command not found).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.simulation.engine_interface import JUNCTIONS, SCENARIOS, SimulationEngine

SUMO_CONFIG = Path(__file__).resolve().parent.parent.parent.parent / "simulation" / "sumo" / "config" / "smartflow.sumocfg"

# Incoming edge to each junction per approach (see simulation/sumo/network/*.xml).
INCOMING_EDGES: dict[str, dict[str, str]] = {
    "J1": {"N": "N1_J1", "S": "J3_J1", "E": "J2_J1", "W": "W1_J1"},
    "J2": {"N": "N2_J2", "S": "J4_J2", "E": "E2_J2", "W": "J1_J2"},
    "J3": {"N": "J1_J3", "S": "S3_J3", "E": "J4_J3", "W": "W3_J3"},
    "J4": {"N": "J2_J4", "S": "S4_J4", "E": "E4_J4", "W": "J3_J4"},
}


def sumo_available() -> tuple[bool, str]:
    if shutil.which("sumo") is None:
        return False, "SUMO binary 'sumo' not found on PATH — install Eclipse SUMO and add its bin/ to PATH"
    try:
        import traci  # noqa: F401
    except ImportError as e:
        return False, f"traci not importable: {e} (SUMO tools/ must be on PYTHONPATH)"
    return True, "ok"


class SumoEngine(SimulationEngine):
    source = "sumo"

    def __init__(self, sumocfg: str | os.PathLike | None = None, gui: bool = False) -> None:
        self.sumocfg = str(sumocfg or SUMO_CONFIG)
        self.gui = gui
        self.running = False
        self.scenario = "normal"
        self.tick = 0
        self._traci = None

    def _connect(self) -> None:
        ok, why = sumo_available()
        if not ok:
            raise RuntimeError(f"SUMO unavailable: {why}")
        import traci

        binary = "sumo-gui" if self.gui else "sumo"
        traci.start([binary, "-c", self.sumocfg, "--start", "--quit-on-end"])
        self._traci = traci

    def start(self, scenario: str = "normal") -> dict:
        self.set_scenario(scenario)
        self._connect()
        self.running = True
        return self.status()

    def pause(self) -> dict:
        self.running = False
        return self.status()

    def reset(self) -> dict:
        self.close()
        self.tick = 0
        return self.status()

    def close(self) -> None:
        if self._traci is not None:
            try:
                self._traci.close()
            except Exception:
                pass
            self._traci = None
        self.running = False

    def set_scenario(self, scenario: str) -> dict:
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario {scenario}")
        self.scenario = scenario
        return self.status()

    def step(self) -> dict:
        if not self.running or self._traci is None:
            return self.snapshot()
        self._traci.simulationStep()
        self.tick += 1
        return self.snapshot()

    def _junction_data(self, jid: str) -> dict:
        traci = self._traci
        counts, queues = {}, {}
        for approach in ("N", "S", "E", "W"):
            lane = f"{INCOMING_EDGES[jid][approach]}_0"
            try:
                counts[approach] = traci.lane.getLastStepVehicleNumber(lane)
                queues[approach] = traci.lane.getLastStepHaltingNumber(lane)
            except Exception:
                counts[approach] = 0
                queues[approach] = 0
        try:
            phase = traci.trafficlight.getPhase(jid)
            phase_name = traci.trafficlight.getPhaseName(jid)
        except Exception:
            phase, phase_name = 0, ""
        return {"counts": counts, "queues": queues, "phase": phase, "phase_name": phase_name}

    def get_phase(self, junction_id: str) -> str:
        return self._junction_data(junction_id)["phase_name"]

    def set_phase(self, junction_id: str, phase_index: int) -> None:
        """Set a TLS phase by index — caller must have validated the
        transition through the signal state machine first."""
        if self._traci is None:
            raise RuntimeError("SUMO not connected")
        self._traci.trafficlight.setPhase(junction_id, phase_index)

    def snapshot(self) -> dict:
        if self._traci is None:
            return {"source": "sumo", "running": False, "scenario": self.scenario,
                    "tick": self.tick, "junctions": {}, "vehicles": []}
        traci = self._traci
        junctions = {j: self._junction_data(j) for j in JUNCTIONS}
        vehicles = []
        for vid in traci.vehicle.getIDList():
            pos = traci.vehicle.getPosition(vid)
            vehicles.append({
                "id": vid, "type": traci.vehicle.getTypeID(vid),
                "x": round(pos[0], 1), "y": round(pos[1], 1),
                "speed_kmh": round(traci.vehicle.getSpeed(vid) * 3.6, 1),
                "waiting_s": round(traci.vehicle.getWaitingTime(vid), 1),
            })
        return {
            "source": "sumo", "running": self.running, "scenario": self.scenario,
            "tick": self.tick,
            "total_vehicles": len(vehicles),
            "junctions": junctions, "vehicles": vehicles,
        }

    def status(self) -> dict:
        ok, why = sumo_available()
        return {
            "source": "sumo", "engine": "SumoEngine", "available": ok,
            "detail": why, "running": self.running,
            "scenario": self.scenario, "tick": self.tick,
            "sumocfg": self.sumocfg,
        }
