"""Fixed-time vs adaptive comparison — simulated engine (NOT SUMO).

Runs Experiment A (fixed-time) and Experiment B (adaptive) with IDENTICAL
inputs: same 2x2 network (J1-J4), same demand process, same seed (42),
same duration (120 ticks), same scenario ("unbalanced"). Only the signal
control strategy differs.

Model (documented, abstract — this is a queue model on top of the same
arrival process the SimulatedEngine uses, NOT a SUMO/TraCI run):
- 1 tick = 1 s. Each junction has 4 approaches (N/S/E/W).
- Arrivals per approach per tick: randint(0, 2) from random.Random(seed)
  (mean 1.0 veh/tick); J1/East gets +randint(0, 2) extra (the engine's
  "unbalanced" pattern), mean 2.0 veh/tick. The SAME arrival stream is
  replayed for both runs (recorded once, then reused).
- Saturation discharge: 3 vehicles per green tick per approach.
- Phase cycle per junction: GREEN -> YELLOW (3 s) -> ALL_RED (2 s) ->
  GREEN (other group). Groups: NS and EW, mutually exclusive.
- Fixed mode: green = 30 s for both groups.
- Adaptive mode: green = demand_for_approach() from the real codebase
  (G = clip(Gmin + k*D, Gmin, Gmax), Gmin=10, Gmax=60, k=0.8, default
  weights) using the busiest approach of the group; StarvationTracker
  forces service after 6 ticks unserved.
- Metrics are COMPUTED from the run: mean queue (vehicle-ticks / ticks),
  max queue, throughput (vehicles discharged), mean wait via Little's law
  (mean_queue / arrival_rate, per approach, averaged).

Results are written to SQLite table simulation_run (mode fixed/adaptive,
status completed) and to backend/data/comparison-<date>.json.
No percentages are invented — the caller computes differences from these.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session  # noqa: E402

from app.database import create_db_and_tables, engine  # noqa: E402
from app.models import SimulationRun  # noqa: E402
from app.services.signal_service import StarvationTracker, demand_for_approach  # noqa: E402

JUNCTIONS = ["J1", "J2", "J3", "J4"]
APPROACHES = ["N", "S", "E", "W"]
GROUPS = {"NS": ["N", "S"], "EW": ["E", "W"]}
SEED = 42
TICKS = 120
SCENARIO = "unbalanced"
YELLOW_S = 3
ALL_RED_S = 2
DISCHARGE_PER_GREEN_TICK = 3  # vehicles per approach per green tick


def build_arrivals(seed: int, ticks: int) -> dict:
    """One identical arrival stream, replayed for both experiments."""
    rng = random.Random(seed)
    arrivals: dict = {}
    for t in range(ticks):
        for j in JUNCTIONS:
            for a in APPROACHES:
                n = rng.randint(0, 2)
                if j == "J1" and a == "E":
                    n += rng.randint(0, 2)
                arrivals[(t, j, a)] = n
    return arrivals


def run_experiment(mode: str, arrivals: dict) -> dict:
    assert mode in ("fixed", "adaptive")
    queues = {j: {a: 0 for a in APPROACHES} for j in JUNCTIONS}
    # per-junction phase state
    phase = {j: "GREEN_NS" for j in JUNCTIONS}
    remaining = {j: 30 for j in JUNCTIONS}  # ticks left in current phase
    green_ns = {j: 30 for j in JUNCTIONS}
    green_ew = {j: 30 for j in JUNCTIONS}
    trackers = {j: StarvationTracker(starvation_ticks=6) for j in JUNCTIONS}
    wait_ticks = {j: {a: 0 for a in APPROACHES} for j in JUNCTIONS}
    departed = {j: {a: 0 for a in APPROACHES} for j in JUNCTIONS}
    total_arrived = {j: {a: 0 for a in APPROACHES} for j in JUNCTIONS}
    queue_samples: list[int] = []
    max_queue = 0
    tick_no = 0
    starved_next: dict[str, str | None] = {j: None for j in JUNCTIONS}

    def group_green(j: str, group: str) -> int:
        if mode == "fixed":
            return 30
        # Adaptive: busiest approach of the group drives the group green.
        best = 0.0
        for a in GROUPS[group]:
            q = queues[j][a]
            avg_wait = (wait_ticks[j][a] / max(1, departed[j][a])) if departed[j][a] else float(q)
            d = demand_for_approach(q, q, avg_wait)
            best = max(best, d["green_s"])
        return int(round(best))

    def start_green(j: str, group: str) -> None:
        g = group_green(j, group)
        if group == "NS":
            green_ns[j] = g
        else:
            green_ew[j] = g
        phase[j] = f"GREEN_{group}"
        remaining[j] = g

    for t in range(TICKS):
        tick_no = t + 1
        for j in JUNCTIONS:
            # arrivals
            for a in APPROACHES:
                n = arrivals[(t, j, a)]
                queues[j][a] += n
                total_arrived[j][a] += n
            # discharge during green
            if phase[j].startswith("GREEN"):
                group = phase[j].split("_")[1]
                for a in GROUPS[group]:
                    served = min(queues[j][a], DISCHARGE_PER_GREEN_TICK)
                    queues[j][a] -= served
                    departed[j][a] += served
            # waiting accumulation + starvation bookkeeping
            for a in APPROACHES:
                wait_ticks[j][a] += queues[j][a]
                max_queue = max(max_queue, queues[j][a])
            queue_samples.append(sum(queues[j][a] for a in APPROACHES))
            # phase clock
            remaining[j] -= 1
            if remaining[j] <= 0:
                if phase[j].startswith("GREEN"):
                    served_group = phase[j].split("_")[1]
                    # StarvationTracker returns the group that must be
                    # served next if it has waited >= 6 ticks unserved.
                    starved_next[j] = trackers[j].tick(served_group, tick_no, ["NS", "EW"])
                    phase[j] = f"YELLOW_{served_group}"
                    remaining[j] = YELLOW_S
                elif phase[j].startswith("YELLOW"):
                    phase[j] = "ALL_RED"
                    remaining[j] = ALL_RED_S
                else:  # ALL_RED -> next green
                    if starved_next.get(j):
                        nxt = starved_next[j]
                    else:
                        nxt = "EW" if _last_green.get(j) == "NS" else "NS"
                    starved_next[j] = None
                    _last_green[j] = nxt
                    start_green(j, nxt)
        # Starvation is enforced in the ALL_RED -> GREEN branch above:
        # a starved group is served next regardless of demand.

    total_departed = sum(sum(d.values()) for d in departed.values())
    total_arr = sum(sum(v.values()) for v in total_arrived.values())
    mean_queue = sum(queue_samples) / len(queue_samples) / len(JUNCTIONS)
    # Little's law per approach, averaged: wait = mean_queue / arrival rate
    waits = []
    for j in JUNCTIONS:
        for a in APPROACHES:
            # Mean wait per discharged vehicle (waiting vehicle-ticks /
            # vehicles discharged); vehicles still queued at the end are
            # excluded, which understates wait slightly — noted in the docs.
            waits.append(wait_ticks[j][a] / max(1, departed[j][a]) if departed[j][a] else 0.0)
    mean_wait = sum(waits) / len(waits)
    return {
        "mode": mode,
        "scenario": SCENARIO,
        "seed": SEED,
        "duration_ticks": TICKS,
        "mean_wait_s": round(mean_wait, 2),
        "mean_queue": round(mean_queue, 2),
        "throughput": total_departed,
        "max_queue": max_queue,
        "total_arrived": total_arr,
        "engine": "simulated (queue model on identical arrival stream; NOT SUMO)",
    }


_last_green: dict[str, str] = {j: "NS" for j in JUNCTIONS}


def main() -> None:
    create_db_and_tables()
    arrivals = build_arrivals(SEED, TICKS)
    results = {}
    with Session(engine) as session:
        for mode in ("fixed", "adaptive"):
            _last_green.update({j: "NS" for j in JUNCTIONS})
            r = run_experiment(mode, arrivals)
            results[mode] = r
            session.add(SimulationRun(
                mode=mode, scenario=SCENARIO, seed=SEED, duration_s=TICKS,
                mean_wait_s=r["mean_wait_s"], mean_queue=r["mean_queue"],
                throughput=r["throughput"], max_queue=r["max_queue"],
                status="completed",
            ))
        session.commit()
        from sqlmodel import select
        rows = session.exec(
            select(SimulationRun).where(SimulationRun.status == "completed")
            .order_by(SimulationRun.id.desc()).limit(2)
        ).all()
        results["run_ids"] = {r.mode: r.id for r in rows}
    out = Path(__file__).resolve().parent.parent / "data" / f"comparison-{date.today()}.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print("saved:", out)


if __name__ == "__main__":
    main()
