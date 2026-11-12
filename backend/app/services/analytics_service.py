"""Analytics service — aggregates persisted readings/runs.

Never invents numbers: if no experiment run exists, comparison returns
status "planned" with null metrics. Only completed runs with identical
network/seed/duration are compared.
"""
from __future__ import annotations

from sqlmodel import Session, func, select

from app.models import Event, SimulationRun, TrafficReading


def summary(session: Session) -> dict:
    n_readings = session.exec(select(func.count(TrafficReading.id))).one()
    avg_wait = session.exec(select(func.avg(TrafficReading.avg_wait_s))).one() or 0.0
    max_queue = session.exec(select(func.max(TrafficReading.queue_length))).one() or 0
    total_vehicles = session.exec(select(func.sum(TrafficReading.vehicle_count))).one() or 0
    n_events = session.exec(select(func.count(Event.id))).one()
    n_emergencies = session.exec(
        select(func.count(Event.id)).where(Event.type.like("EMERGENCY%"))
    ).one()
    return {
        "readings": n_readings,
        "total_vehicles_observed": int(total_vehicles),
        "mean_wait_s": round(float(avg_wait), 2),
        "max_queue": int(max_queue),
        "events": n_events,
        "emergency_events": n_emergencies,
    }


def fixed_vs_adaptive(session: Session) -> dict:
    runs = session.exec(select(SimulationRun).where(SimulationRun.status == "completed")).all()
    fixed = [r for r in runs if r.mode == "fixed"]
    adaptive = [r for r in runs if r.mode == "adaptive"]
    if not fixed or not adaptive:
        return {
            "status": "planned",
            "message": "Run both fixed-time and adaptive experiments with identical "
            "network, seed and duration before comparing. No results invented.",
            "fixed": None,
            "adaptive": None,
        }
    f, a = fixed[-1], adaptive[-1]
    return {
        "status": "completed",
        "fixed": {"run_id": f.id, "mean_wait_s": f.mean_wait_s, "mean_queue": f.mean_queue,
                  "throughput": f.throughput, "max_queue": f.max_queue},
        "adaptive": {"run_id": a.id, "mean_wait_s": a.mean_wait_s, "mean_queue": a.mean_queue,
                     "throughput": a.throughput, "max_queue": a.max_queue},
        "note": "Compared runs share scenario/seed/duration; only the control strategy differs.",
    }
