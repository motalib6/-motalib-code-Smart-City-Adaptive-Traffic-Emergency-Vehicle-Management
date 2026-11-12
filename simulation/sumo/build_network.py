#!/usr/bin/env python3
"""Build the SUMO network: netconvert nodes+edges -> smartflow.net.xml.

Requires Eclipse SUMO on PATH (`netconvert --version`).
Run from the repo root:  python simulation/sumo/build_network.py
NOT verified in this VM — SUMO is not installed here.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    for tool in ("netconvert", "sumo"):
        r = subprocess.run([tool, "--version"], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"FAIL: {tool} not available — install Eclipse SUMO first.")
            return 1
        print(r.stdout.strip().splitlines()[0])
    cmd = [
        "netconvert",
        "--node-files", str(HERE / "network" / "smartflow.nod.xml"),
        "--edge-files", str(HERE / "network" / "smartflow.edg.xml"),
        "--output-file", str(HERE / "network" / "smartflow.net.xml"),
        "--tls.guess", "true",
        "--no-turnarounds", "true",
    ]
    print("Running:", " ".join(cmd))
    r = subprocess.run(cmd, text=True)
    if r.returncode != 0:
        print("FAIL: netconvert failed — see output above.")
        return r.returncode
    print("PASS: network written to simulation/sumo/network/smartflow.net.xml")
    print("Verify with: sumo-gui -c simulation/sumo/config/smartflow.sumocfg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
