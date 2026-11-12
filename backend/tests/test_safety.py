"""Unit tests: conflict matrix + signal state machine (yellow/all-red never skipped)."""
import pytest

from app.safety.conflict_matrix import is_safe_transition, phases_conflict
from app.safety.signal_state_machine import IllegalTransitionError, SignalStateMachine


def test_conflicting_greens_detected():
    assert phases_conflict("GREEN_NS", "GREEN_EW") is True
    assert phases_conflict("GREEN_NS", "GREEN_NS") is False


def test_direct_green_to_green_is_unsafe():
    assert is_safe_transition("GREEN_NS", "GREEN_EW") is False
    assert is_safe_transition("GREEN_NS", "YELLOW_NS") is True


def test_full_phase_sequence():
    m = SignalStateMachine("J1")
    assert m.phase == "GREEN_NS"
    for expected in ["YELLOW_NS", "ALL_RED", "GREEN_EW", "YELLOW_EW", "ALL_RED", "GREEN_NS"]:
        assert m.transition(m.next_phase()) == expected


def test_illegal_skip_raises():
    m = SignalStateMachine("J1")
    with pytest.raises(IllegalTransitionError):
        m.transition("GREEN_EW")  # skipping YELLOW_NS + ALL_RED


def test_emergency_safe_switch_walks_clearance():
    m = SignalStateMachine("J1", "GREEN_NS")
    steps = m.force_safe_switch("GREEN_EW")
    assert steps == ["YELLOW_NS", "ALL_RED", "GREEN_EW"]
    assert m.phase == "GREEN_EW"


def test_emergency_safe_switch_noop_when_already_green():
    m = SignalStateMachine("J1", "GREEN_EW")
    assert m.force_safe_switch("GREEN_EW") == []
