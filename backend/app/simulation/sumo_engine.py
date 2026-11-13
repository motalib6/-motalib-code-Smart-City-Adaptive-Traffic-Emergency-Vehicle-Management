"""Real SUMO engine via TraCI with telemetry extraction.

Implements SimulationEngine interface using real Eclipse SUMO and TraCI.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from app.simulation.engine_interface import JUNCTIONS, SCENARIOS, SimulationEngine
from app.simulation.junction_mapper import JunctionMapper
from app.simulation.telemetry_collector import TelemetryCollector
from app.simulation.emergency_priority_manager import EmergencyPriorityManager

# Default config path
SUMO_CONFIG = Path(__file__).resolve().parent.parent.parent.parent / "simulation" / "sumo" / "config" / "smartflow.sumocfg"


def sumo_available() -> tuple[bool, str]:
    """Check whether SUMO binaries and Python TraCI are properly available."""
    # Check binary from settings or environment
    from app.config import settings
    sumo_bin = os.environ.get("SUMO_BINARY", settings.sumo_binary)
    if not os.path.exists(sumo_bin) and shutil.which("sumo") is None:
        return False, f"SUMO binary 'sumo' not found at {sumo_bin} or on PATH — install Eclipse SUMO and add its bin/ to PATH"

    try:
        import traci  # noqa: F401
    except ImportError:
        sumo_home = os.environ.get("SUMO_HOME", settings.sumo_home)
        tools_path = os.path.join(sumo_home, "tools")
        if os.path.exists(tools_path):
            import sys
            if tools_path not in sys.path:
                sys.path.insert(0, tools_path)
            try:
                import traci  # noqa: F401
            except ImportError as e:
                return False, f"traci not importable from {tools_path}: {e}"
        else:
            return False, f"SUMO tools directory not found at {tools_path}"
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
        self.mapper = JunctionMapper()
        self.collector = TelemetryCollector(self.mapper)
        self.emergency_manager = EmergencyPriorityManager(self.mapper)
        self._latest_snapshot: dict[str, Any] = {}

    def _connect(self) -> None:
        ok, why = sumo_available()
        if not ok:
            raise RuntimeError(f"SUMO unavailable: {why}")
        import traci

        if not os.path.exists(self.sumocfg):
            # Check relative to backend/
            alt = Path(__file__).resolve().parent.parent.parent / "simulation" / "sumo" / "config" / "smartflow.sumocfg"
            # Check relative to workspace root (parent of parent)
            alt_root = Path(__file__).resolve().parent.parent.parent.parent / "simulation" / "sumo" / "config" / "smartflow.sumocfg"
            if alt.exists():
                self.sumocfg = str(alt)
            elif alt_root.exists():
                self.sumocfg = str(alt_root)
            else:
                raise FileNotFoundError(f"SUMO configuration file not found at {self.sumocfg}")

        from app.config import settings
        binary = os.environ.get("SUMO_GUI_BINARY" if self.gui else "SUMO_BINARY")
        if not binary or not os.path.exists(binary):
            binary = "sumo-gui" if self.gui else "sumo"

        cmd = [binary, "-c", self.sumocfg, "--start", "--quit-on-end"]
        traci.start(cmd)
        self._traci = traci

    def start(self, scenario: str = "normal") -> dict:
        self.set_scenario(scenario)
        if self._traci is None:
            self._connect()
        self.running = True
        return self.status()

    def pause(self) -> dict:
        self.running = False
        return self.status()

    def reset(self) -> dict:
        self.close()
        self.tick = 0
        self._latest_snapshot = {}
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

        # Advance emergency preemption lifecycle
        emergency_updates = self.emergency_manager.step_controller(self._traci)

        self._latest_snapshot = self.collector.collect_network_telemetry(self._traci, self.tick, self.scenario)
        if emergency_updates:
            self._latest_snapshot["emergency_updates"] = emergency_updates
        return self._latest_snapshot

    def get_phase(self, junction_id: str) -> str:
        sumo_id = self.mapper.to_sumo_id(junction_id)
        if self._traci is None:
            return ""
        try:
            phase_idx = self._traci.trafficlight.getPhase(sumo_id)
            phase_name_map = {0: "GREEN_NS", 1: "YELLOW_NS", 2: "GREEN_EW", 3: "YELLOW_EW"}
            return phase_name_map.get(phase_idx, "ALL_RED")
        except Exception:
            return ""

    def set_phase(self, junction_id: str, phase_index: int) -> None:
        """Set a TLS phase by index."""
        if self._traci is None:
            raise RuntimeError("SUMO not connected")
        sumo_id = self.mapper.to_sumo_id(junction_id)
        self._traci.trafficlight.setPhase(sumo_id, phase_index)

    def snapshot(self) -> dict:
        if self._traci is None:
            return {
                "source": "sumo",
                "running": False,
                "scenario": self.scenario,
                "tick": self.tick,
                "total_vehicles": 0,
                "waiting_to_depart": 0,
                "avg_wait_s": 0.0,
                "junctions": {},
                "vehicles": [],
            }
        if not self._latest_snapshot:
            self._latest_snapshot = self.collector.collect_network_telemetry(self._traci, self.tick, self.scenario)
        return self._latest_snapshot

    def status(self) -> dict:
        ok, why = sumo_available()
        return {
            "source": "sumo",
            "engine": "SumoEngine",
            "available": ok,
            "detail": why,
            "running": self.running,
            "scenario": self.scenario,
            "tick": self.tick,
            "sumocfg": self.sumocfg,
        }
