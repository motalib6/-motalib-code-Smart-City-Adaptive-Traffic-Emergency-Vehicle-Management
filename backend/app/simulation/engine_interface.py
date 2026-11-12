"""Simulation engine interface — one contract for SUMO and simulated engines."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

SCENARIOS = ["normal", "medium", "rush", "heavy", "unbalanced", "emergency"]
JUNCTIONS = ["J1", "J2", "J3", "J4"]


class SimulationEngine(ABC):
    source: str = "unknown"  # "sumo" | "simulated" — always reported to clients

    @abstractmethod
    def start(self, scenario: str = "normal") -> dict: ...

    @abstractmethod
    def pause(self) -> dict: ...

    @abstractmethod
    def reset(self) -> dict: ...

    @abstractmethod
    def set_scenario(self, scenario: str) -> dict: ...

    @abstractmethod
    def step(self) -> dict:
        """Advance one tick and return the live snapshot."""

    @abstractmethod
    def snapshot(self) -> dict: ...

    @abstractmethod
    def status(self) -> dict: ...
