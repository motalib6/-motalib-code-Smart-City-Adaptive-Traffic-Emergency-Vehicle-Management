"""Generate multi-scenario routes for SMARTFLOW ODISHA using randomTrips.py and duarouter."""
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NET_FILE = BASE_DIR / "network" / "smartflow.net.xml"
ROUTES_DIR = BASE_DIR / "routes"
ROUTES_DIR.mkdir(parents=True, exist_ok=True)
ROU_FILE = ROUTES_DIR / "smartflow.rou.xml"
TRIPS_FILE = ROUTES_DIR / "smartflow.trips.xml"

SCENARIOS = {
    "normal": {"period": "2.5", "seed": 42},
    "medium": {"period": "1.8", "seed": 43},
    "rush": {"period": "1.0", "seed": 44},
    "heavy": {"period": "0.6", "seed": 45},
}

def generate_routes(scenario="normal"):
    sumo_home = os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\SUMO")
    random_trips = os.path.join(sumo_home, "tools", "randomTrips.py")
    cfg = SCENARIOS.get(scenario, SCENARIOS["normal"])

    cmd = [
        "python",
        random_trips,
        "-n", str(NET_FILE),
        "-r", str(ROU_FILE),
        "-o", str(TRIPS_FILE),
        "-p", cfg["period"],
        "-e", "3600",
        "--seed", str(cfg["seed"]),
        "--fringe-factor", "5",
        "--min-distance", "100",
        "--validate",
        "--vehicle-class", "passenger",
    ]
    print("Generating routes with:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error generating routes:", res.stderr)
        raise RuntimeError(res.stderr)
    print("Routes generated successfully at", ROU_FILE)

if __name__ == "__main__":
    generate_routes("normal")
