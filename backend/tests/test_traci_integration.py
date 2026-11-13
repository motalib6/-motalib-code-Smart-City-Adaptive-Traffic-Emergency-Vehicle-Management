"""
Real TraCI and SimulationManager integration test for SMARTFLOW ODISHA.
Tests:
1. sumo_available() reports True and detected valid binaries/tools.
2. SumoEngine starts SUMO using real config.
3. Advance simulation with step() and verify TraCI simulationStep.
4. TelemetryCollector captures vehicle IDs, position, speed, queues, lane occupancy.
5. Traffic-light IDs and states retrieved correctly.
6. Junction mapping resolves J1..J4 to A0..B1 and back.
7. SimulationManager thread-safe command queue (start, pause, resume, reset).
8. MockEngine fallback isolation.
"""
import asyncio
import os
import sys

# Ensure backend in PYTHONPATH
BACKEND_DIR = os.path.abspath("smartflow-odisha/backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.simulation import (
    SumoEngine,
    SimulatedEngine,
    MockEngine,
    SimulationManager,
    sumo_available,
    JunctionMapper,
    TelemetryCollector,
)

async def run_traci_tests():
    test_results = []

    def record(name: str, passed: bool, details: str = ""):
        test_results.append({"name": name, "passed": passed, "details": details})
        print(f"[{'PASS' if passed else 'FAIL'}] {name} - {details}")

    # TEST 1: Check SUMO installation & TraCI import
    ok, why = sumo_available()
    record("SUMO Availability", ok, f"sumo_available={ok}, detail={why}")
    if not ok:
        print("Cannot continue TraCI test since SUMO is unavailable.")
        return test_results

    # TEST 2: JunctionMapper bidirectional mapping
    mapper = JunctionMapper()
    j1_sumo = mapper.to_sumo_id("J1")
    j1_back = mapper.to_app_id(j1_sumo)
    approach_e = mapper.get_incoming_edge("J1", "E")
    record(
        "Junction Mapping",
        j1_sumo == "A0" and j1_back == "J1" and approach_e == "B0A0",
        f"J1 -> {j1_sumo} -> {j1_back}, incoming E: {approach_e}"
    )

    # TEST 3: SumoEngine Start & Connect
    engine = SumoEngine(gui=False)
    st = engine.start("normal")
    record(
        "SumoEngine Start",
        engine.running and engine._traci is not None,
        f"running={engine.running}, source={engine.source}"
    )

    # TEST 4: Step Simulation & Collect Telemetry
    telemetry_samples = []
    for _ in range(30):
        t = engine.step()
        telemetry_samples.append(t)

    last_t = telemetry_samples[-1]
    total_vehs = last_t.get("total_vehicles", 0)
    sim_time = last_t.get("sim_time_s", 0.0)
    tls = last_t.get("traffic_lights", {})
    junctions = last_t.get("junctions", {})

    record(
        "TraCI Step & SimTime",
        sim_time >= 30.0 and engine.tick == 30,
        f"sim_time={sim_time}s, tick={engine.tick}"
    )

    record(
        "Vehicle Telemetry Retrieval",
        total_vehs > 0 and len(last_t.get("vehicles", [])) == total_vehs,
        f"Active vehicles retrieved: {total_vehs}"
    )

    record(
        "Traffic Light IDs & States",
        len(tls) == 4 and all(k in tls for k in ["A0", "A1", "B0", "B1"]),
        f"TLS IDs: {list(tls.keys())}"
    )

    # Check junction metrics
    j1_data = junctions.get("J1", {})
    has_metrics = "counts" in j1_data and "queues" in j1_data and "occupancy" in j1_data
    record(
        "Junction Metrics (Counts, Queues, Occupancy)",
        has_metrics,
        f"J1 counts: {j1_data.get('counts')}, queues: {j1_data.get('queues')}"
    )

    # TEST 5: Close engine cleanly
    engine.close()
    record("SumoEngine Close", not engine.running and engine._traci is None, "TraCI connection closed.")

    # TEST 6: SimulationManager Command Queue (Thread-safe TraCI owner)
    received_telemetry = []
    async def tele_cb(data):
        received_telemetry.append(data)

    mgr = SimulationManager(default_engine_type="sumo", gui=False, telemetry_callback=tele_cb)
    await mgr.start_worker()

    # Start via command queue
    start_res = await mgr.start(scenario="normal", engine="sumo")
    record(
        "SimulationManager Start Command",
        start_res.get("status") == "started" and mgr._running,
        f"status={start_res.get('status')}, running={mgr._running}"
    )

    # Allow worker to step
    await asyncio.sleep(3.5)

    # Pause via command queue
    pause_res = await mgr.pause()
    record(
        "SimulationManager Pause Command",
        pause_res.get("status") == "paused" and mgr._paused,
        f"paused={mgr._paused}"
    )

    # Resume via command queue
    resume_res = await mgr.resume()
    record(
        "SimulationManager Resume Command",
        resume_res.get("status") == "resumed" and not mgr._paused,
        f"resumed={not mgr._paused}"
    )

    await asyncio.sleep(2.0)

    # Reset via command queue
    reset_res = await mgr.reset()
    record(
        "SimulationManager Reset Command",
        reset_res.get("status") == "reset" and mgr._tick == 0,
        f"reset tick={mgr._tick}"
    )

    # Stop manager worker
    await mgr.stop_worker()
    record(
        "SimulationManager Stop Worker",
        mgr.worker_task is None,
        "Worker loop terminated safely."
    )

    # TEST 7: MockEngine / SimulatedEngine Fallback Verification
    mock = MockEngine()
    mock_st = mock.start("normal")
    mock_snap = mock.step()
    record(
        "MockEngine Fallback Isolation",
        mock.source == "simulated" and mock.running and mock_snap["source"] == "simulated",
        f"MockEngine verified as distinct fallback (source={mock.source})"
    )

    return test_results

if __name__ == "__main__":
    results = asyncio.run(run_traci_tests())
    failures = [r for r in results if not r["passed"]]
    print(f"\nFinal Test Summary: {len(results) - len(failures)}/{len(results)} passed.")
    if failures:
        sys.exit(1)
