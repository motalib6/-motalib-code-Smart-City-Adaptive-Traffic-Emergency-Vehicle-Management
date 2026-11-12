"""Deterministic seeded in-process simulation engine.

Source label is ALWAYS "simulated" — never claim this is SUMO. Same
interface as SumoEngine so the frontend/backend behave identically; only
the data source differs. Seeded RNG => reproducible runs (fixed vs adaptive
experiments use the same seed).
"""
from __future__ import annotations

import random
from typing import Any

from app.simulation.engine_interface import JUNCTIONS, SCENARIOS, SimulationEngine

# Mean vehicles spawned per tick per junction, per scenario.
SCENARIO_RATE = {
    "normal": 2, "medium": 4, "rush": 8, "heavy": 12,
    "unbalanced": 3, "emergency": 3,
}
VEHICLE_TYPES = ["car", "car", "car", "motorcycle", "bus", "truck"]


class SimulatedEngine(SimulationEngine):
    source = "simulated"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.scenario = "normal"
        self.running = False
        self.tick = 0
        self._vehicles: dict[str, dict] = {}
        self._vid = 0
        self.counts: dict[str, dict[str, int]] = {
            j: {"N": 0, "S": 0, "E": 0, "W": 0} for j in JUNCTIONS
        }
        self.queues: dict[str, dict[str, int]] = {
            j: {"N": 0, "S": 0, "E": 0, "W": 0} for j in JUNCTIONS
        }
        self.wait_s: dict[str, float] = {j: 0.0 for j in JUNCTIONS}

    # -- lifecycle -------------------------------------------------------
    def start(self, scenario: str = "normal") -> dict:
        self.set_scenario(scenario)
        self.running = True
        return self.status()

    def pause(self) -> dict:
        self.running = False
        return self.status()

    def reset(self) -> dict:
        self.__init__(seed=self.seed)
        return self.status()

    def set_scenario(self, scenario: str) -> dict:
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario {scenario}; valid: {SCENARIOS}")
        self.scenario = scenario
        return self.status()

    # -- stepping --------------------------------------------------------
    def step(self) -> dict:
        if not self.running:
            return self.snapshot()
        self.tick += 1
        rate = SCENARIO_RATE[self.scenario]
        for j in JUNCTIONS:
            for approach in ("N", "S", "E", "W"):
                spawn = self.rng.randint(0, rate)
                # Unbalanced: east approach at J1 carries most traffic.
                if self.scenario == "unbalanced" and j == "J1" and approach == "E":
                    spawn += rate
                depart = self.rng.randint(0, max(1, self.counts[j][approach]))
                self.counts[j][approach] = max(0, self.counts[j][approach] + spawn - depart)
                self.queues[j][approach] = max(0, self.counts[j][approach] - depart)
                self.wait_s[j] = round(
                    max(0.0, self.wait_s[j] + self.rng.uniform(-1, 2)), 1
                )
                for _ in range(spawn):
                    self._vid += 1
                    vtype = self.rng.choice(VEHICLE_TYPES)
                    self._vehicles[f"veh-{self._vid}"] = {
                        "id": f"veh-{self._vid}", "type": vtype,
                        "junction": j, "approach": approach,
                        "x": round(self.rng.uniform(0, 800), 1),
                        "y": round(self.rng.uniform(0, 800), 1),
                        "speed_kmh": round(self.rng.uniform(0, 50), 1),
                        "waiting_s": round(self.rng.uniform(0, 20), 1),
                    }
        if self.scenario == "emergency" and self.tick % 5 == 0:
            self._vid += 1
            self._vehicles[f"amb-{self._vid}"] = {
                "id": f"amb-{self._vid}", "type": "ambulance", "junction": "J1",
                "approach": "E", "x": 100.0, "y": 400.0,
                "speed_kmh": 45.0, "waiting_s": 0.0,
            }
        # Cap retained vehicles (memory-bounded demo).
        if len(self._vehicles) > 400:
            keys = sorted(self._vehicles)[: len(self._vehicles) - 400]
            for k in keys:
                del self._vehicles[k]
        return self.snapshot()

    def snapshot(self) -> dict:
        total = sum(sum(c.values()) for c in self.counts.values())
        return {
            "source": "simulated",
            "running": self.running,
            "scenario": self.scenario,
            "tick": self.tick,
            "seed": self.seed,
            "total_vehicles": total,
            "junctions": {
                j: {
                    "counts": dict(self.counts[j]),
                    "queues": dict(self.queues[j]),
                    "avg_wait_s": self.wait_s[j],
                    "total": sum(self.counts[j].values()),
                }
                for j in JUNCTIONS
            },
            "vehicles": list(self._vehicles.values())[:200],
        }

    def status(self) -> dict:
        return {
            "source": "simulated",
            "engine": "SimulatedEngine",
            "available": True,
            "running": self.running,
            "scenario": self.scenario,
            "tick": self.tick,
            "note": "Deterministic seeded in-process simulation. NOT SUMO.",
        }
