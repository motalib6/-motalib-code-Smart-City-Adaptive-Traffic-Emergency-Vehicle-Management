"""Validate SMARTFLOW SUMO network, signals, routes, and run headless simulation verification."""
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NET_FILE = BASE_DIR / "network" / "smartflow.net.xml"
CFG_FILE = BASE_DIR / "config" / "smartflow.sumocfg"

def validate():
    print("=== 1. Validating Network XML ===")
    assert NET_FILE.exists(), f"Network file missing: {NET_FILE}"
    tree = ET.parse(NET_FILE)
    root = tree.getroot()

    tls_nodes = [j.get("id") for j in root.findall("junction") if j.get("type") == "traffic_light"]
    print(f"Detected Traffic Light Junctions: {tls_nodes}")
    assert set(tls_nodes) == {"A0", "A1", "B0", "B1"}, f"Expected 4 TLS nodes A0, A1, B0, B1, got: {tls_nodes}"

    tl_logics = [tl.get("id") for tl in root.findall("tlLogic")]
    print(f"Detected tlLogic programs: {tl_logics}")
    assert set(tl_logics) == {"A0", "A1", "B0", "B1"}, f"Expected 4 tlLogic programs, got: {tl_logics}"

    print("\n=== 2. Validating SUMO Headless Execution (10 steps) ===")
    sumo_home = os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\SUMO")
    sumo_bin = os.path.join(sumo_home, "bin", "sumo.exe")
    if not os.path.exists(sumo_bin):
        sumo_bin = "sumo"

    cmd = [sumo_bin, "-c", str(CFG_FILE), "--end", "10", "--no-step-log", "true"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Headless run failed: {res.stderr}"
    print("Headless SUMO simulation completed 10 steps successfully.")

    print("\n=== All Validations Passed! ===")

if __name__ == "__main__":
    validate()
