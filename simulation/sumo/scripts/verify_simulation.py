"""
Headless and TraCI verification script for SMARTFLOW Odisha SUMO network.
Tests:
- TraCI connectivity
- Junction and Traffic Light ID retrieval
- Active vehicle insertion
- Nonzero vehicle velocities (vehicles actually move)
- Traffic light state inspection
"""
import os
import sys
import json

sumo_home = os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\SUMO")
tools_path = os.path.join(sumo_home, "tools")
if tools_path not in sys.path:
    sys.path.append(tools_path)

import traci  # noqa: E402

def run_headless_traci_test(steps=120):
    config_file = os.path.abspath("simulation/sumo/config/smartflow.sumocfg")
    mapping_file = os.path.abspath("simulation/sumo/network/junction_mapping.json")

    with open(mapping_file, "r") as f:
        mapping = json.load(f)

    sumo_cmd = ["sumo", "-c", config_file]
    print(f"Starting SUMO with: {sumo_cmd}")
    traci.start(sumo_cmd)

    tls_ids = set(traci.trafficlight.getIDList())
    junction_ids = set(traci.junction.getIDList())

    print(f"TraCI loaded {len(junction_ids)} junctions and {len(tls_ids)} traffic lights.")
    print(f"Actual SUMO TLS IDs: {sorted(list(tls_ids))}")

    # Check mapping
    for app_id, meta in mapping["junctions"].items():
        s_id = meta["sumo_tls_id"]
        assert s_id in tls_ids, f"Traffic light {s_id} for {app_id} not found in SUMO!"
        assert meta["sumo_junction_id"] in junction_ids, f"Junction {meta['sumo_junction_id']} for {app_id} not in SUMO!"

    speeds = []
    positions = []
    total_vehicles_seen = set()

    for step in range(1, steps + 1):
        traci.simulationStep()
        active_vehs = traci.vehicle.getIDList()
        total_vehicles_seen.update(active_vehs)

        for vid in active_vehs:
            spd = traci.vehicle.getSpeed(vid)
            speeds.append(spd)

        if step in [1, 30, 60, 90, 120]:
            print(f"Step {step:3d}: Active Vehicles={len(active_vehs):2d}, Unique Observed={len(total_vehicles_seen):2d}")

    # Verify vehicle movement
    moving_speeds = [s for s in speeds if s > 0.1]
    max_speed = max(speeds) if speeds else 0.0
    avg_speed = sum(speeds) / len(speeds) if speeds else 0.0

    print(f"\nMovement Verification:")
    print(f"- Total active vehicle speed samples: {len(speeds)}")
    print(f"- Moving samples (> 0.1 m/s): {len(moving_speeds)}")
    print(f"- Average Speed: {avg_speed:.2f} m/s ({avg_speed * 3.6:.2f} km/h)")
    print(f"- Max Speed: {max_speed:.2f} m/s ({max_speed * 3.6:.2f} km/h)")
    print(f"- Total distinct vehicles simulated: {len(total_vehicles_seen)}")

    assert len(total_vehicles_seen) > 0, "No vehicles were inserted into simulation!"
    assert len(moving_speeds) > 0, "Vehicles were inserted but did not move!"

    # Verify traffic light query
    print("\nTraffic Light Status Verification:")
    for app_id, meta in mapping["junctions"].items():
        s_tls = meta["sumo_tls_id"]
        phase_idx = traci.trafficlight.getPhase(s_tls)
        state_str = traci.trafficlight.getRedYellowGreenState(s_tls)
        print(f"- [{app_id}] {meta['app_label']:15} -> TLS '{s_tls}': Phase={phase_idx}, State={state_str}")

    traci.close()
    print("\nHeadless TraCI test PASSED successfully.")

if __name__ == "__main__":
    run_headless_traci_test()
