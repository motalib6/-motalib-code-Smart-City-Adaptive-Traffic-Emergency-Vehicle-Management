"""Traffic service — density score.

D_i = w1*Q_i + w2*N_i + w3*W_i
  Q = queue length, N = vehicle count, W = average waiting time (s).
Weights are configurable via admin settings; defaults w1=0.5, w2=0.3, w3=0.2.
"""
from __future__ import annotations


def density_score(
    queue_length: int,
    vehicle_count: int,
    avg_wait_s: float,
    w_queue: float = 0.5,
    w_count: float = 0.3,
    w_wait: float = 0.2,
) -> float:
    if queue_length < 0 or vehicle_count < 0 or avg_wait_s < 0:
        raise ValueError("traffic inputs must be non-negative")
    return w_queue * queue_length + w_count * vehicle_count + w_wait * avg_wait_s


def congestion_level(density: float) -> str:
    if density < 5:
        return "free"
    if density < 15:
        return "moderate"
    if density < 30:
        return "congested"
    return "severe"
