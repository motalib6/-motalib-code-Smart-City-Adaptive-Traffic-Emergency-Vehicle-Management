"""Signal state machine.

GREEN_NS -> YELLOW_NS -> ALL_RED -> GREEN_EW -> YELLOW_EW -> ALL_RED -> GREEN_NS
Every transition is validated by the conflict matrix; yellow and all-red
clearance phases are NEVER skipped, including for emergency priority.
"""
from __future__ import annotations

from app.safety.conflict_matrix import is_safe_transition

SEQUENCE = ["GREEN_NS", "YELLOW_NS", "ALL_RED", "GREEN_EW", "YELLOW_EW", "ALL_RED"]
# Next legal phase after each phase (ALL_RED goes to the opposite green,
# decided by the caller via `next_after_all_red`).
NEXT = {
    "GREEN_NS": "YELLOW_NS",
    "YELLOW_NS": "ALL_RED",
    "GREEN_EW": "YELLOW_EW",
    "YELLOW_EW": "ALL_RED",
}


class IllegalTransitionError(ValueError):
    pass


class SignalStateMachine:
    def __init__(self, junction_id: str, initial: str = "GREEN_NS") -> None:
        self.junction_id = junction_id
        self.phase = initial
        self.history: list[str] = [initial]

    def next_phase(self) -> str:
        """The single legal successor of the current phase."""
        if self.phase == "ALL_RED":
            # Direction is chosen by the controller; default alternates to EW
            # unless the last green was EW (tracked via history).
            last_green = next(
                (p for p in reversed(self.history) if p in ("GREEN_NS", "GREEN_EW")),
                "GREEN_NS",
            )
            return "GREEN_EW" if last_green == "GREEN_NS" else "GREEN_NS"
        return NEXT[self.phase]

    def transition(self, to_phase: str) -> str:
        """Advance one legal step. Raises IllegalTransitionError on any skip
        (e.g. GREEN_NS -> GREEN_EW) or conflicting green."""
        expected = self.next_phase()
        if to_phase != expected:
            raise IllegalTransitionError(
                f"{self.junction_id}: illegal transition {self.phase} -> {to_phase}; "
                f"expected {expected} (yellow/all-red must not be skipped)"
            )
        if not is_safe_transition(self.phase, to_phase):
            raise IllegalTransitionError(
                f"{self.junction_id}: conflicting green {self.phase} -> {to_phase}"
            )
        self.phase = to_phase
        self.history.append(to_phase)
        return self.phase

    def force_safe_switch(self, target_green: str) -> list[str]:
        """Safely switch to a target green (used by emergency priority):
        walks the full sequence GREEN -> YELLOW -> ALL_RED -> target green,
        returning every intermediate phase. Never jumps directly."""
        if target_green not in ("GREEN_NS", "GREEN_EW"):
            raise IllegalTransitionError(f"target must be a green phase, got {target_green}")
        steps: list[str] = []
        if self.phase == target_green:
            return steps
        while self.phase != target_green:
            nxt = self.next_phase()
            if self.phase == "ALL_RED":
                nxt = target_green
            steps.append(self.transition(nxt))
        return steps
