"""Real WebSocket client test for ws://127.0.0.1:8000/ws/live.

Connects, waits for live messages while the simulation is running, and
prints/saves the first simulation_tick message verbatim. Exits non-zero
if no tick message arrives within the timeout.
Usage: .venv/bin/python scripts/ws_test.py [--timeout 20] [--out path]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

import websockets

URL = "ws://127.0.0.1:8000/ws/live"


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    got: list[dict] = []
    try:
        async with websockets.connect(URL, open_timeout=10) as ws:
            print("connected to", URL)
            try:
                while len(got) < 3:
                    raw = await asyncio.wait_for(ws.recv(), timeout=args.timeout)
                    msg = json.loads(raw)
                    got.append(msg)
                    print("MSG:", json.dumps(msg)[:600])
                    if msg.get("type") == "simulation_tick":
                        break
            except asyncio.TimeoutError:
                print("TIMEOUT waiting for messages")
    except Exception as e:  # noqa: BLE001
        print("WS ERROR:", repr(e))
        return 2
    tick = next((m for m in got if m.get("type") == "simulation_tick"), None)
    if tick is None:
        print("FAIL: no simulation_tick message received")
        return 1
    if args.out:
        with open(args.out, "w") as f:
            json.dump(tick, f, indent=2)
        print("saved tick message to", args.out)
    # Note: manager.broadcast puts payload fields at top level (no "data" wrapper).
    print("PASS: simulation_tick tick=%s total_vehicles=%s junctions=%s source=%s" % (
        tick.get("tick"), tick.get("total_vehicles"),
        sorted((tick.get("junctions") or {}).keys()), tick.get("source")))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
