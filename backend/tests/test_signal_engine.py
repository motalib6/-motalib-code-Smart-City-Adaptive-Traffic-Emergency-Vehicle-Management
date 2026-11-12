"""Unit tests: density score, adaptive timing bounds, starvation prevention."""
import pytest

from app.services.signal_service import StarvationTracker, adaptive_green, demand_for_approach
from app.services.traffic_service import congestion_level, density_score


def test_density_formula():
    # D = 0.5*10 + 0.3*20 + 0.2*30 = 5 + 6 + 6 = 17
    assert density_score(10, 20, 30.0) == pytest.approx(17.0)


def test_density_rejects_negative():
    with pytest.raises(ValueError):
        density_score(-1, 0, 0.0)


def test_timing_bounds():
    assert adaptive_green(0) == 10.0  # Gmin floor
    assert adaptive_green(1000) == 60.0  # Gmax ceiling
    assert adaptive_green(25) == pytest.approx(30.0)  # 10 + 0.8*25


def test_timing_grows_with_density():
    assert adaptive_green(20) > adaptive_green(5)


def test_demand_for_approach_shape():
    d = demand_for_approach(5, 10, 4.0)
    assert set(d) == {"density", "green_s"}
    assert 10.0 <= d["green_s"] <= 60.0


def test_starvation_prevention():
    tracker = StarvationTracker(starvation_ticks=3)
    # Serve NS for 3 ticks while EW waits.
    assert tracker.tick("NS", 1, ["NS", "EW"]) is None
    assert tracker.tick("NS", 2, ["NS", "EW"]) is None
    assert tracker.tick("NS", 3, ["NS", "EW"]) is None
    assert tracker.tick("NS", 4, ["NS", "EW"]) == "EW"


def test_congestion_levels():
    assert congestion_level(2) == "free"
    assert congestion_level(10) == "moderate"
    assert congestion_level(20) == "congested"
    assert congestion_level(50) == "severe"
