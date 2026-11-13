"""Generate SMARTFLOW ODISHA 2x2 grid network with 4 controlled junctions using SUMO netgenerate/netconvert."""
import os
import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NET_DIR = BASE_DIR / "network"
NET_DIR.mkdir(parents=True, exist_ok=True)
NET_FILE = NET_DIR / "smartflow.net.xml"
MAPPING_FILE = NET_DIR / "junction_mapping.json"

def generate_network():
    sumo_home = os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\SUMO")
    netgenerate = os.path.join(sumo_home, "bin", "netgenerate.exe")
    if not os.path.exists(netgenerate):
        netgenerate = "netgenerate"

    # Generate 2x2 grid with traffic lights at all 4 internal junctions (A0, A1, B0, B1)
    cmd = [
        netgenerate,
        "--grid",
        "--grid.x-number=2",
        "--grid.y-number=2",
        "--grid.x-length=300",
        "--grid.y-length=300",
        "--grid.attach-length=150",
        "--default.lanenumber=2",
        "--default.speed=13.89",
        "--tls.guess=true",
        "--tls.default-type=static",
        "--output-file=" + str(NET_FILE),
    ]
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error:", res.stderr)
        raise RuntimeError("netgenerate failed: " + res.stderr)
    print("Network generated successfully at", NET_FILE)

    mapping = {
        "description": "Mapping between SMARTFLOW application junction labels and actual SUMO network junction / traffic light IDs",
        "network_file": "simulation/sumo/network/smartflow.net.xml",
        "junctions": {
            "J1": {
                "app_label": "Rasulgarh",
                "sumo_junction_id": "A0",
                "sumo_tls_id": "A0",
                "type": "traffic_light",
                "coordinates": {"x": 150.0, "y": 150.0},
                "grid_position": "bottom-left"
            },
            "J2": {
                "app_label": "Vani Vihar",
                "sumo_junction_id": "A1",
                "sumo_tls_id": "A1",
                "type": "traffic_light",
                "coordinates": {"x": 150.0, "y": 450.0},
                "grid_position": "top-left"
            },
            "J3": {
                "app_label": "Master Canteen",
                "sumo_junction_id": "B0",
                "sumo_tls_id": "B0",
                "type": "traffic_light",
                "coordinates": {"x": 450.0, "y": 150.0},
                "grid_position": "bottom-right"
            },
            "J4": {
                "app_label": "Khandagiri",
                "sumo_junction_id": "B1",
                "sumo_tls_id": "B1",
                "type": "traffic_light",
                "coordinates": {"x": 450.0, "y": 450.0},
                "grid_position": "top-right"
            }
        }
    }
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print("Mapping saved to", MAPPING_FILE)

if __name__ == "__main__":
    generate_network()
