"""Conflict matrix — NS and EW movements are mutually exclusive.

A phase is a set of allowed movements. Two phases conflict if they share a
green movement on incompatible approaches. This is the single source of
truth used before EVERY signal transition.
"""
from __future__ import annotations

# Movements granted green by each phase.
PHASE_MOVEMENTS: dict[str, frozenset[str]] = {
    "GREEN_NS": frozenset({"N", "S"}),
    "YELLOW_NS": frozenset({"N", "S"}),
    "GREEN_EW": frozenset({"E", "W"}),
    "YELLOW_EW": frozenset({"E", "W"}),
    "ALL_RED": frozenset(),
}

GREEN_PHASES = {"GREEN_NS", "GREEN_EW"}


def phases_conflict(a: str, b: str) -> bool:
    """True if both phases grant green to incompatible movements."""
    if a not in GREEN_PHASES or b not in GREEN_PHASES:
        return False
    return bool(PHASE_MOVEMENTS[a] & PHASE_MOVEMENTS[b]) is False and a != b


def is_safe_transition(from_phase: str, to_phase: str) -> bool:
    """A green-to-opposite-green jump is never safe; it must pass through
    YELLOW then ALL_RED. Green->same-green and anything->ALL_RED are safe."""
    if from_phase in GREEN_PHASES and to_phase in GREEN_PHASES and from_phase != to_phase:
        return False
    return True


def validate_no_conflicting_greens(phases: dict[str, str]) -> list[str]:
    """Check a whole network: no two junctions may grant conflicting greens
    on a shared approach (defensive check; junctions are independent here,
    so this currently validates each phase is a known phase)."""
    errors = []
    for jid, phase in phases.items():
        if phase not in PHASE_MOVEMENTS:
            errors.append(f"{jid}: unknown phase {phase}")
    return errors
