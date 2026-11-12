"""Adaptive signal service.

Green duration:  G = clip(Gmin + k*D, Gmin, Gmax)
Starvation prevention: an approach unserved for >= starvation_ticks gets
priority on the next cycle regardless of demand.
"""
from __future__ import annotations

from app.services.traffic_service import density_score


def adaptive_green(
    density: float,
    green_min: float = 10.0,
    green_max: float = 60.0,
    k: float = 0.8,
) -> float:
    return max(green_min, min(green_max, green_min + k * density))


def demand_for_approach(
    queue_length: int,
    vehicle_count: int,
    avg_wait_s: float,
    weights: dict | None = None,
) -> dict:
    w = weights or {}
    d = density_score(
        queue_length, vehicle_count, avg_wait_s,
        w.get("w_queue", 0.5), w.get("w_count", 0.3), w.get("w_wait", 0.2),
    )
    green = adaptive_green(
        d,
        w.get("green_min_s", 10.0),
        w.get("green_max_s", 60.0),
        w.get("demand_k", 0.8),
    )
    return {"density": round(d, 2), "green_s": round(green, 1)}


class StarvationTracker:
    """Tracks ticks since each approach last had green; forces service."""

    def __init__(self, starvation_ticks: int = 6) -> None:
        self.starvation_ticks = starvation_ticks
        self.waiting_since: dict[str, int] = {}

    def tick(self, served: str, tick: int, approaches: list[str]) -> str | None:
        """Record one cycle. Returns the starved approach (if any) that must
        be served next, else None."""
        for a in approaches:
            if a == served:
                self.waiting_since[a] = tick
            elif a not in self.waiting_since:
                self.waiting_since[a] = tick
        for a in approaches:
            if a != served and tick - self.waiting_since.get(a, tick) >= self.starvation_ticks:
                self.waiting_since[a] = tick
                return a
        return None
