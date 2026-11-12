"""Emergency service — route validation, ETA, safe priority decisions.

Priority is NEVER granted by jumping a conflicting green. The caller must
walk the signal state machine (GREEN -> YELLOW -> ALL_RED -> green) via
SignalStateMachine.force_safe_switch(); this module validates the route
and computes ETA / next-junction preparation.
"""
from __future__ import annotations

VALID_JUNCTIONS = {"J1", "J2", "J3", "J4"}
# Adjacency of the 2x2 network (J1 top-left, J2 top-right, J3 bottom-left, J4 bottom-right)
ADJACENCY: dict[str, set[str]] = {
    "J1": {"J2", "J3"},
    "J2": {"J1", "J4"},
    "J3": {"J1", "J4"},
    "J4": {"J2", "J3"},
}
# Approach (N/S/E/W) the ambulance uses when arriving at each junction pair.
APPROACH_FOR_LEG: dict[tuple[str, str], str] = {
    ("J1", "J2"): "E", ("J2", "J1"): "W",
    ("J1", "J3"): "S", ("J3", "J1"): "N",
    ("J2", "J4"): "S", ("J4", "J2"): "N",
    ("J3", "J4"): "E", ("J4", "J3"): "W",
}
EDGE_LENGTH_M = 400.0  # simulated edge length between adjacent junctions


class InvalidRouteError(ValueError):
    pass


def validate_route(route: list[str]) -> list[str]:
    if len(route) < 2:
        raise InvalidRouteError("route needs at least current and destination junction")
    for j in route:
        if j not in VALID_JUNCTIONS:
            raise InvalidRouteError(f"unknown junction in route: {j}")
    for a, b in zip(route, route[1:]):
        if b not in ADJACENCY[a]:
            raise InvalidRouteError(f"no direct road {a} -> {b}")
    return route


def approach_for_leg(from_j: str, to_j: str) -> str:
    return APPROACH_FOR_LEG[(from_j, to_j)]


def green_for_approach(approach: str) -> str:
    return "GREEN_NS" if approach in ("N", "S") else "GREEN_EW"


def eta_seconds(distance_m: float, speed_kmh: float) -> float:
    if speed_kmh <= 0:
        raise ValueError("speed must be positive")
    return round(distance_m / (speed_kmh * 1000 / 3600), 1)


def next_junction(route: list[str], current: str) -> str | None:
    try:
        i = route.index(current)
    except ValueError:
        return None
    return route[i + 1] if i + 1 < len(route) else None
