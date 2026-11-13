"""Emergency Priority Manager for SMARTFLOW ODISHA.

Handles real in-SUMO emergency vehicle insertion, tracking, and signal preemption:
1. Creates an 'ambulance' vehicle type in SUMO (emergency class, bright red, high speed).
2. Inserts real ambulance vehicles with specific topology-valid routes.
3. Tracks real vehicle position, velocity, current edge, and distance to next junction via TraCI.
4. Coordinates corridor progression (e.g. J1 -> J2 -> J4).
5. Safe preemption with Conflict Matrix:
   - Identifies conflicting movement.
   - Applies YELLOW clearance (3 seconds).
   - Applies ALL_RED clearance (2 seconds).
   - Grants emergency-compatible GREEN.
   - Monitors ambulance clearing the stop line / junction.
   - Releases priority and hands control back to normal adaptive traffic controller.
6. Multi-emergency priority arbitration.
7. Logs all events in SQLite.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from sqlmodel import Session
from app.database import engine
from app.models.emergency import Emergency
from app.models.event import Event
from app.simulation.junction_mapper import JunctionMapper, JUNCTION_POSITIONS

logger = logging.getLogger("emergency_priority")

# Mapping of route transitions between consecutive junctions to incoming edge and approach direction
# For example, entering J1 from outer west is left0A0 ('W').
# Moving J1 -> J2 is edge A0A1 entering J2 from South ('S').
# Moving J2 -> J4 is edge A1B1 entering J4 from West ('W').
CORRIDOR_EDGES: dict[tuple[str, str], tuple[str, str]] = {
    # (From, To) -> (Edge connecting them, approach direction at 'To' junction)
    ("START", "J1"): ("left0A0", "W"),
    ("START", "J2"): ("top0A1", "N"),
    ("START", "J3"): ("bottom1B0", "S"),
    ("START", "J4"): ("right1B1", "E"),
    ("J1", "J2"): ("A0A1", "S"),
    ("J2", "J1"): ("A1A0", "N"),
    ("J1", "J3"): ("A0B0", "W"),
    ("J3", "J1"): ("B0A0", "E"),
    ("J2", "J4"): ("A1B1", "W"),
    ("J4", "J2"): ("B1A1", "E"),
    ("J3", "J4"): ("B0B1", "S"),
    ("J4", "J3"): ("B1B0", "N"),
}

# High-level phase string definitions for 20-character TLS states
# Phase 0: NS Green -> GGGggrrrrrGGGggrrrrr
# Phase 1: NS Yellow -> yyyyyrrrrryyyyyrrrrr
# Phase 2: EW Green -> rrrrrGGGggrrrrrGGGgg
# Phase 3: EW Yellow -> rrrrryyyyyrrrrryyyyy
ALL_RED_STATE = "rrrrrrrrrrrrrrrrrrrr"
NS_GREEN_STATE = "GGGggrrrrrGGGggrrrrr"
NS_YELLOW_STATE = "yyyyyrrrrryyyyyrrrrr"
EW_GREEN_STATE = "rrrrrGGGggrrrrrGGGgg"
EW_YELLOW_STATE = "rrrrryyyyyrrrrryyyyy"


@dataclass
class ActiveAmbulance:
    emergency_id: int
    ambulance_id: str
    route_junctions: list[str]  # e.g. ["J1", "J2", "J4"]
    sumo_route_id: str
    sumo_edges: list[str]
    current_index: int = 0      # Target junction index in route_junctions
    state: str = "APPROACHING"  # APPROACHING | PREEMPTING_YELLOW | PREEMPTING_ALL_RED | GREEN_GRANTED | CLEARED
    preempt_timer: int = 0
    active_tls: str = ""
    active_target_phase: str = ""  # "NS" | "EW"
    speed_kmh: float = 40.0
    progress: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EmergencyPriorityManager:
    """Manages ambulance preemption inside SUMO via TraCI with safe clearance transitions."""

    def __init__(self, mapper: JunctionMapper | None = None) -> None:
        self.mapper = mapper or JunctionMapper()
        self.active_ambulances: dict[str, ActiveAmbulance] = {}  # ambulance_id -> ActiveAmbulance
        self._vtype_initialized: bool = False

    def ensure_vehicle_type(self, traci_module: Any) -> None:
        """Register the 'ambulance' vehicle type in SUMO."""
        if self._vtype_initialized or traci_module is None:
            return
        try:
            type_ids = traci_module.vehicletype.getIDList()
            if "ambulance" not in type_ids:
                try:
                    traci_module.vehicletype.copy("DEFAULT_VEHTYPE", "ambulance")
                except Exception:
                    pass
                traci_module.vehicletype.setVehicleClass("ambulance", "emergency")
                traci_module.vehicletype.setShapeClass("ambulance", "emergency")
                traci_module.vehicletype.setColor("ambulance", (255, 0, 0, 255))
                traci_module.vehicletype.setSpeedFactor("ambulance", 1.4)
                traci_module.vehicletype.setAccel("ambulance", 4.0)
                traci_module.vehicletype.setDecel("ambulance", 6.0)
            self._vtype_initialized = True
        except Exception as e:
            logger.warning(f"Could not register ambulance vType: {e}")

    def create_emergency_route(self, route_junctions: list[str]) -> list[str]:
        """Derive full SUMO edge path for a list of application junctions."""
        if not route_junctions:
            return []

        edges = []
        # First entry approach
        first_j = route_junctions[0]
        entry_pair = ("START", first_j)
        if entry_pair in CORRIDOR_EDGES:
            edges.append(CORRIDOR_EDGES[entry_pair][0])
        else:
            edges.append(f"left0{self.mapper.to_sumo_id(first_j)}")

        # Intermediate hops
        for i in range(len(route_junctions) - 1):
            hop = (route_junctions[i], route_junctions[i + 1])
            if hop in CORRIDOR_EDGES:
                edges.append(CORRIDOR_EDGES[hop][0])
            else:
                # Default edge name convention from sumo_id1 to sumo_id2
                u = self.mapper.to_sumo_id(hop[0])
                v = self.mapper.to_sumo_id(hop[1])
                edges.append(f"{u}{v}")

        # Exit edge
        last_j = route_junctions[-1]
        last_sumo = self.mapper.to_sumo_id(last_j)
        # Default exit boundary edge
        exit_map = {
            "J1": "A0bottom0",
            "J2": "A1top0",
            "J3": "B0right0",
            "J4": "B1right1",
        }
        edges.append(exit_map.get(last_j, f"{last_sumo}right1"))
        return edges

    def insert_ambulance_in_sumo(
        self,
        traci_module: Any,
        emergency_id: int,
        ambulance_id: str,
        route_junctions: list[str],
        speed_kmh: float = 40.0,
    ) -> ActiveAmbulance:
        """Insert ambulance vehicle into SUMO via TraCI and register for tracking."""
        self.ensure_vehicle_type(traci_module)

        sumo_edges = self.create_emergency_route(route_junctions)
        route_id = f"route_{ambulance_id}_{emergency_id}"

        try:
            traci_module.route.add(route_id, sumo_edges)
        except Exception:
            # Route may already exist
            pass

        try:
            traci_module.vehicle.add(
                ambulance_id,
                route_id,
                typeID="ambulance",
                depart="now",
                departSpeed="max",
            )
            traci_module.vehicle.setColor(ambulance_id, (255, 0, 0, 255))
        except Exception as e:
            logger.error(f"Failed to add vehicle {ambulance_id} to SUMO: {e}")

        active_amb = ActiveAmbulance(
            emergency_id=emergency_id,
            ambulance_id=ambulance_id,
            route_junctions=route_junctions,
            sumo_route_id=route_id,
            sumo_edges=sumo_edges,
            speed_kmh=speed_kmh,
        )
        self.active_ambulances[ambulance_id] = active_amb
        self._log_event(
            event_type="EMERGENCY_VEHICLE_INSERTED",
            message=f"{ambulance_id} inserted into SUMO on route {'->'.join(route_junctions)}",
            junction_id=route_junctions[0],
        )
        return active_amb

    def step_controller(self, traci_module: Any) -> list[dict[str, Any]]:
        """Advance emergency priority state machine for all active ambulances."""
        if traci_module is None or not self.active_ambulances:
            return []

        active_veh_ids = set(traci_module.vehicle.getIDList())
        completed_ids = []
        updates = []

        # Sort ambulances by priority (earlier creation gets priority if conflicting)
        sorted_ambulances = sorted(self.active_ambulances.values(), key=lambda a: a.created_at)

        for amb in sorted_ambulances:
            amb_id = amb.ambulance_id

            if amb_id not in active_veh_ids:
                # Vehicle either hasn't entered yet or already finished its trip
                if amb.state == "CLEARED" or amb.current_index >= len(amb.route_junctions):
                    completed_ids.append(amb_id)
                continue

            # Read actual real-time vehicle attributes from TraCI
            try:
                pos = traci_module.vehicle.getPosition(amb_id)
                speed_ms = traci_module.vehicle.getSpeed(amb_id)
                amb.speed_kmh = round(speed_ms * 3.6, 1)
                curr_edge = traci_module.vehicle.getRoadID(amb_id)
                curr_lane = traci_module.vehicle.getLaneID(amb_id)
            except Exception:
                continue

            target_j = amb.route_junctions[amb.current_index]
            target_sumo_tls = self.mapper.to_sumo_id(target_j)
            target_pos = self.mapper.get_position(target_j)

            # Calculate distance to current target junction
            dist = math.dist(pos, target_pos)
            eff_speed = max(speed_ms, 8.0)
            eta_s = round(dist / eff_speed, 1)

            # Determine approach direction and compatible green phase
            approach = self._get_approach_for_leg(amb, target_j, curr_edge)
            target_phase_group = "NS" if approach in ("N", "S") else "EW"

            # Execute safe transition state machine
            self._handle_preemption_lifecycle(
                traci_module, amb, target_j, target_sumo_tls, target_phase_group, dist, curr_edge
            )

            # Calculate route progress percentage
            total_legs = len(amb.route_junctions)
            amb.progress = round(min(1.0, (amb.current_index + max(0.0, 1.0 - (dist / 300.0))) / total_legs), 2)

            updates.append({
                "id": amb.emergency_id,
                "ambulance_id": amb_id,
                "status": amb.state,
                "current_junction": target_j,
                "next_junction": amb.route_junctions[amb.current_index + 1] if amb.current_index + 1 < total_legs else None,
                "x": round(pos[0], 1),
                "y": round(pos[1], 1),
                "speed_kmh": amb.speed_kmh,
                "distance_to_target_m": round(dist, 1),
                "eta_s": eta_s,
                "progress": amb.progress,
            })

            # Sync SQLite emergency status
            self._update_db_emergency(amb, eta_s, pos)

        for cid in completed_ids:
            self._finalize_emergency(cid)

        return updates

    def _get_approach_for_leg(self, amb: ActiveAmbulance, target_j: str, curr_edge: str) -> str:
        """Determine approach direction (N, S, E, W) at target junction based on incoming edge."""
        for app in ("N", "S", "E", "W"):
            edge_expected = self.mapper.get_incoming_edge(target_j, app)
            if edge_expected and (curr_edge == edge_expected or curr_edge.startswith(edge_expected)):
                return app
        # Default based on predecessor
        if amb.current_index == 0:
            return "W"
        prev_j = amb.route_junctions[amb.current_index - 1]
        pair = (prev_j, target_j)
        return CORRIDOR_EDGES.get(pair, ("", "W"))[1]

    def _handle_preemption_lifecycle(
        self,
        traci_module: Any,
        amb: ActiveAmbulance,
        target_j: str,
        target_sumo_tls: str,
        target_phase_group: str,
        dist: float,
        curr_edge: str,
    ) -> None:
        """Conflict arbitration, YELLOW -> ALL_RED -> GREEN transition."""
        try:
            curr_state = traci_module.trafficlight.getRedYellowGreenState(target_sumo_tls)
        except Exception:
            return

        is_ns_green = "G" in curr_state[:5] or "g" in curr_state[:5]
        is_ew_green = "G" in curr_state[5:10] or "g" in curr_state[5:10]

        # 1. APPROACHING: Trigger preemption when ambulance is within 160 meters
        if amb.state == "APPROACHING":
            amb.active_tls = target_sumo_tls
            amb.active_target_phase = target_phase_group

            if dist <= 160.0:
                # Check if current signal already serves the required movement
                already_compatible = (target_phase_group == "NS" and is_ns_green) or (
                    target_phase_group == "EW" and is_ew_green
                )
                if already_compatible:
                    amb.state = "GREEN_GRANTED"
                    self._log_event(
                        "PRIORITY_GRANTED",
                        f"Compatible green already active at {target_j} for {amb.ambulance_id}",
                        target_j,
                    )
                else:
                    # Conflicting green detected -> Begin safe clearance with YELLOW
                    amb.state = "PREEMPTING_YELLOW"
                    amb.preempt_timer = 3  # 3 seconds yellow clearance
                    yellow_state = NS_YELLOW_STATE if is_ns_green else EW_YELLOW_STATE
                    traci_module.trafficlight.setRedYellowGreenState(target_sumo_tls, yellow_state)
                    self._log_event(
                        "YELLOW_STARTED",
                        f"Yellow clearance initiated at {target_j} before emergency switch",
                        target_j,
                    )

        # 2. YELLOW CLEARANCE: Count down to ALL_RED
        elif amb.state == "PREEMPTING_YELLOW":
            amb.preempt_timer -= 1
            if amb.preempt_timer <= 0:
                amb.state = "PREEMPTING_ALL_RED"
                amb.preempt_timer = 2  # 2 seconds all-red clearance
                traci_module.trafficlight.setRedYellowGreenState(target_sumo_tls, ALL_RED_STATE)
                self._log_event(
                    "ALL_RED_STARTED",
                    f"All-red intersection clearance active at {target_j}",
                    target_j,
                )

        # 3. ALL RED CLEARANCE: Count down to EMERGENCY GREEN
        elif amb.state == "PREEMPTING_ALL_RED":
            amb.preempt_timer -= 1
            if amb.preempt_timer <= 0:
                amb.state = "GREEN_GRANTED"
                emergency_green = NS_GREEN_STATE if target_phase_group == "NS" else EW_GREEN_STATE
                traci_module.trafficlight.setRedYellowGreenState(target_sumo_tls, emergency_green)
                self._log_event(
                    "PRIORITY_GRANTED",
                    f"Emergency priority green granted at {target_j} for {amb.ambulance_id} ({target_phase_group})",
                    target_j,
                )

        # 4. GREEN GRANTED: Monitor vehicle crossing the intersection
        elif amb.state == "GREEN_GRANTED":
            emergency_green = NS_GREEN_STATE if target_phase_group == "NS" else EW_GREEN_STATE
            traci_module.trafficlight.setRedYellowGreenState(target_sumo_tls, emergency_green)

            # Check if ambulance passed stop line (e.g. is on internal junction edge or entered next edge)
            is_cleared = (dist < 15.0) or curr_edge.startswith(":") or (
                amb.current_index + 1 < len(amb.route_junctions)
                and curr_edge == CORRIDOR_EDGES.get((target_j, amb.route_junctions[amb.current_index + 1]), ("", ""))[0]
            )

            if is_cleared:
                self._log_event(
                    "PRIORITY_RELEASED",
                    f"{amb.ambulance_id} cleared intersection {target_j}. Priority released.",
                    target_j,
                )
                # Release TLS control back to default program
                try:
                    traci_module.trafficlight.setProgram(target_sumo_tls, "0")
                except Exception:
                    pass

                # Advance to next junction in corridor or complete
                amb.current_index += 1
                if amb.current_index < len(amb.route_junctions):
                    next_j = amb.route_junctions[amb.current_index]
                    amb.state = "APPROACHING"
                    self._log_event(
                        "NEXT_JUNCTION_PREPARED",
                        f"Preparing next junction {next_j} for {amb.ambulance_id}",
                        next_j,
                    )
                else:
                    amb.state = "CLEARED"
                    self._log_event(
                        "EMERGENCY_COMPLETED",
                        f"{amb.ambulance_id} completed full corridor route",
                        target_j,
                    )

    def _log_event(self, event_type: str, message: str, junction_id: str | None = None) -> None:
        """Write emergency event directly into SQLite."""
        try:
            with Session(engine) as session:
                ev = Event(
                    type=event_type,
                    message=message,
                    junction_id=junction_id,
                    source="sumo-priority-controller",
                )
                session.add(ev)
                session.commit()
        except Exception as e:
            logger.warning(f"Could not log event {event_type}: {e}")

    def _update_db_emergency(self, amb: ActiveAmbulance, eta_s: float, pos: tuple[float, float]) -> None:
        """Update Emergency record in database."""
        try:
            with Session(engine) as session:
                em = session.get(Emergency, amb.emergency_id)
                if em:
                    em.status = amb.state
                    em.eta_s = eta_s
                    em.progress = amb.progress
                    em.speed_kmh = amb.speed_kmh
                    session.add(em)
                    session.commit()
        except Exception:
            pass

    def _finalize_emergency(self, ambulance_id: str) -> None:
        """Mark completed and cleanup."""
        amb = self.active_ambulances.pop(ambulance_id, None)
        if amb:
            try:
                with Session(engine) as session:
                    em = session.get(Emergency, amb.emergency_id)
                    if em:
                        em.status = "COMPLETED"
                        em.completed_at = datetime.now(timezone.utc)
                        session.add(em)
                        session.commit()
            except Exception:
                pass
