"""Telemetry Collector — extracts live SUMO/TraCI metrics into structured schemas.

Extracts:
1. Active vehicle list (id, type, position x/y, speed km/h, waiting time s)
2. Lane-wise vehicle counts and queues
3. Lane occupancy percentage
4. Total waiting time and average delay
5. Traffic-light IDs and states
6. Simulation time and vehicles waiting to depart
"""
from __future__ import annotations

from typing import Any
from app.simulation.junction_mapper import JunctionMapper, JUNCTION_POSITIONS


class TelemetryCollector:
    """Collects and aggregates live network telemetry from TraCI."""

    def __init__(self, mapper: JunctionMapper | None = None) -> None:
        self.mapper = mapper or JunctionMapper()

    def collect_network_telemetry(self, traci_module: Any, tick: int, scenario: str) -> dict[str, Any]:
        """Query TraCI for full system snapshot."""
        if traci_module is None:
            return {
                "source": "sumo",
                "running": False,
                "scenario": scenario,
                "tick": tick,
                "total_vehicles": 0,
                "waiting_to_depart": 0,
                "sim_time_s": 0.0,
                "junctions": {},
                "vehicles": [],
                "traffic_lights": {},
            }

        sim_time = traci_module.simulation.getTime()
        waiting_to_depart = traci_module.simulation.getLoadedNumber() - traci_module.simulation.getDepartedNumber()
        if waiting_to_depart < 0:
            waiting_to_depart = 0

        # 1. Collect vehicles
        veh_ids = traci_module.vehicle.getIDList()
        vehicles = []
        total_waiting_time = 0.0

        for vid in veh_ids:
            try:
                pos = traci_module.vehicle.getPosition(vid)
                spd = traci_module.vehicle.getSpeed(vid)
                wait_s = traci_module.vehicle.getWaitingTime(vid)
                total_waiting_time += wait_s
                vehicles.append({
                    "id": vid,
                    "type": traci_module.vehicle.getTypeID(vid),
                    "x": round(pos[0], 1),
                    "y": round(pos[1], 1),
                    "speed_kmh": round(spd * 3.6, 1),
                    "speed_ms": round(spd, 2),
                    "waiting_s": round(wait_s, 1),
                    "lane_id": traci_module.vehicle.getLaneID(vid),
                })
            except Exception:
                continue

        avg_wait_s = round(total_waiting_time / len(vehicles), 2) if vehicles else 0.0

        # 2. Collect Traffic Lights
        tls_ids = traci_module.trafficlight.getIDList()
        tls_data = {}
        for tls_id in tls_ids:
            try:
                state_str = traci_module.trafficlight.getRedYellowGreenState(tls_id)
                phase_idx = traci_module.trafficlight.getPhase(tls_id)
                tls_data[tls_id] = {
                    "phase": phase_idx,
                    "state": state_str,
                }
            except Exception:
                continue

        # 3. Collect Junction-wise counts, queues, occupancy
        junctions = {}
        for app_id in ("J1", "J2", "J3", "J4"):
            sumo_id = self.mapper.to_sumo_id(app_id)
            counts: dict[str, int] = {}
            queues: dict[str, int] = {}
            occupancy: dict[str, float] = {}
            waiting_times: dict[str, float] = {}

            j_total_count = 0
            j_total_wait = 0.0

            for approach in ("N", "S", "E", "W"):
                edge_id = self.mapper.get_incoming_edge(app_id, approach)
                lane_count = 0
                lane_queue = 0
                lane_occ = 0.0
                lane_wait = 0.0

                if edge_id:
                    # In our 2-lane setup, check both lane 0 and lane 1
                    for lane_idx in (0, 1):
                        lane_id = f"{edge_id}_{lane_idx}"
                        try:
                            lane_count += traci_module.lane.getLastStepVehicleNumber(lane_id)
                            lane_queue += traci_module.lane.getLastStepHaltingNumber(lane_id)
                            lane_occ = max(lane_occ, traci_module.lane.getLastStepOccupancy(lane_id) * 100.0)
                            lane_wait += traci_module.lane.getWaitingTime(lane_id)
                        except Exception:
                            pass

                counts[approach] = lane_count
                queues[approach] = lane_queue
                occupancy[approach] = round(lane_occ, 2)
                waiting_times[approach] = round(lane_wait, 1)

                j_total_count += lane_count
                j_total_wait += lane_wait

            j_avg_wait = round(j_total_wait / j_total_count, 1) if j_total_count > 0 else 0.0

            # TLS state for this junction
            tl_info = tls_data.get(sumo_id, {"phase": 0, "state": ""})

            # Derive high-level phase label (GREEN_NS, YELLOW_NS, GREEN_EW, YELLOW_EW, ALL_RED)
            phase_idx = tl_info["phase"]
            # Phase 0: GGGggrrrrrGGGggrrrrr (NS Green)
            # Phase 1: yyyyyrrrrryyyyyrrrrr (NS Yellow)
            # Phase 2: rrrrrGGGggrrrrrGGGgg (EW Green)
            # Phase 3: rrrrryyyyyrrrrryyyyy (EW Yellow)
            phase_name_map = {
                0: "GREEN_NS",
                1: "YELLOW_NS",
                2: "GREEN_EW",
                3: "YELLOW_EW",
            }
            phase_label = phase_name_map.get(phase_idx, "ALL_RED")

            x_pos, y_pos = self.mapper.get_position(app_id)

            junctions[app_id] = {
                "id": app_id,
                "name": self.mapper.get_junction_name(app_id),
                "sumo_id": sumo_id,
                "x": x_pos,
                "y": y_pos,
                "counts": counts,
                "queues": queues,
                "occupancy": occupancy,
                "waiting_times": waiting_times,
                "total": j_total_count,
                "avg_wait_s": j_avg_wait,
                "phase": phase_idx,
                "phase_name": phase_label,
                "tls_state": tl_info["state"],
            }

        return {
            "source": "sumo",
            "running": True,
            "scenario": scenario,
            "tick": tick,
            "sim_time_s": sim_time,
            "total_vehicles": len(vehicles),
            "waiting_to_depart": waiting_to_depart,
            "avg_wait_s": avg_wait_s,
            "junctions": junctions,
            "vehicles": vehicles,
            "traffic_lights": tls_data,
        }
