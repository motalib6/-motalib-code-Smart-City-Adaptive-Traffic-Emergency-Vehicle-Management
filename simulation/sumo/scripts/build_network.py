"""
Network generation and route creation script for SMARTFLOW ODISHA.
Orchestrates:
1. netgenerate to produce a 2x2 grid network with 4 central TLS controlled junctions.
2. randomTrips.py to generate repeatable demand with duarouter route validation.
3. Generates simulation/sumo/network/junction_mapping.json.
4. Generates simulation/sumo/config/smartflow.sumocfg.
"""
import os
import sys
import json
import subprocess
import xml.etree.ElementTree as ET

SUMO_HOME = os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\SUMO")
TOOLS_PATH = os.path.join(SUMO_HOME, "tools")
RANDOM_TRIPS = os.path.join(TOOLS_PATH, "randomTrips.py")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NETWORK_DIR = os.path.join(BASE_DIR, "network")
ROUTES_DIR = os.path.join(BASE_DIR, "routes")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

NET_FILE = os.path.join(NETWORK_DIR, "smartflow.net.xml")
TRIP_FILE = os.path.join(ROUTES_DIR, "smartflow.trips.xml")
ROU_FILE = os.path.join(ROUTES_DIR, "smartflow.rou.xml")
CFG_FILE = os.path.join(CONFIG_DIR, "smartflow.sumocfg")
MAPPING_FILE = os.path.join(NETWORK_DIR, "junction_mapping.json")

def generate_network():
    print("[1/4] Running netgenerate for 2x2 grid with TLS guessing...")
    cmd = [
        "netgenerate",
        "--grid",
        "--grid.number=2",
        "--grid.length=300",
        "--grid.attach-length=150",
        "--default.lanenumber=2",
        "--tls.guess",
        "--tls.guess.threshold=0",
        f"--output-file={NET_FILE}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"netgenerate failed: {res.stderr}")
    print(f"Network generated at: {NET_FILE}")

def inspect_and_map_junctions():
    print("[2/4] Inspecting XML and mapping junctions...")
    tree = ET.parse(NET_FILE)
    root = tree.getroot()

    tls_nodes = {}
    for tl in root.findall("tlLogic"):
        tls_nodes[tl.get("id")] = tl.get("type")

    # The 4 internal grid junctions in a 2x2 grid
    # A0=(150, 150), A1=(150, 450), B0=(450, 150), B1=(450, 450)
    app_mapping = {
        "J1": {"label": "Rasulgarh", "sumo_id": "A0", "pos": "bottom-left"},
        "J2": {"label": "Vani Vihar", "sumo_id": "A1", "pos": "top-left"},
        "J3": {"label": "Master Canteen", "sumo_id": "B0", "pos": "bottom-right"},
        "J4": {"label": "Khandagiri", "sumo_id": "B1", "pos": "top-right"},
    }

    junctions_dict = {}
    sumo_to_app = {}

    for app_id, info in app_mapping.items():
        sid = info["sumo_id"]
        j_elem = root.find(f".//junction[@id='{sid}']")
        if j_elem is None:
            raise RuntimeError(f"Junction {sid} not found in generated network XML!")
        if sid not in tls_nodes:
            raise RuntimeError(f"Junction {sid} does not have a traffic light logic!")

        incoming = [e.get("id") for e in root.findall(f".//edge[@to='{sid}']") if not e.get("id").startswith(":")]
        outgoing = [e.get("id") for e in root.findall(f".//edge[@from='{sid}']") if not e.get("id").startswith(":")]

        junctions_dict[app_id] = {
            "app_label": info["label"],
            "sumo_junction_id": sid,
            "sumo_tls_id": sid,
            "type": j_elem.get("type"),
            "coordinates": {
                "x": float(j_elem.get("x")),
                "y": float(j_elem.get("y"))
            },
            "grid_position": info["pos"],
            "incoming_edges": incoming,
            "outgoing_edges": outgoing
        }
        sumo_to_app[sid] = app_id

    boundary_nodes = []
    for j in root.findall("junction"):
        jid = j.get("id")
        if not jid.startswith(":") and jid not in sumo_to_app:
            boundary_nodes.append({
                "id": jid,
                "x": float(j.get("x")),
                "y": float(j.get("y")),
                "type": j.get("type")
            })

    output_mapping = {
        "description": "Mapping between SMARTFLOW application junction labels and actual SUMO network junction / traffic light IDs",
        "generated_at": "2026-11-12T13:30:00+05:30",
        "network_file": "simulation/sumo/network/smartflow.net.xml",
        "junctions": junctions_dict,
        "sumo_to_app": sumo_to_app,
        "boundary_nodes": boundary_nodes
    }

    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(output_mapping, f, indent=2)
    print(f"Mapping written to: {MAPPING_FILE}")

def generate_routes():
    print("[3/4] Running randomTrips.py for repeatable traffic demand...")
    cmd = [
        sys.executable,
        RANDOM_TRIPS,
        "-n", NET_FILE,
        "-r", ROU_FILE,
        "-o", TRIP_FILE,
        "-b", "0",
        "-e", "3600",
        "-p", "2.0",
        "--seed", "42",
        "--validate",
        "--fringe-factor", "5",
        "--min-distance", "100"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"randomTrips.py failed: {res.stderr}\n{res.stdout}")
    print(f"Validated routes written to: {ROU_FILE}")

def generate_sumocfg():
    print("[4/4] Writing smartflow.sumocfg...")
    sumocfg_content = """<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="../network/smartflow.net.xml"/>
        <route-files value="../routes/smartflow.rou.xml"/>
    </input>

    <time>
        <begin value="0"/>
        <end value="3600"/>
        <step-length value="1.0"/>
    </time>

    <processing>
        <collision.action value="none"/>
        <time-to-teleport value="300"/>
    </processing>

    <report>
        <verbose value="false"/>
        <no-step-log value="true"/>
    </report>

    <gui_only>
        <start value="true"/>
        <quit-on-end value="false"/>
    </gui_only>
</configuration>
"""
    with open(CFG_FILE, "w", encoding="utf-8") as f:
        f.write(sumocfg_content)
    print(f"Configuration written to: {CFG_FILE}")

if __name__ == "__main__":
    generate_network()
    inspect_and_map_junctions()
    generate_routes()
    generate_sumocfg()
    print("SUMO Network pipeline completed successfully.")
