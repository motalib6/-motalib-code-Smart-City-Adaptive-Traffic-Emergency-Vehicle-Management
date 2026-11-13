"""Simulation subpackage for SMARTFLOW ODISHA.

Exposes:
- SimulationEngine (interface)
- SumoEngine (real TraCI)
- SimulatedEngine (mock/fallback engine)
- SimulationManager (thread-safe execution controller)
- TelemetryCollector
- JunctionMapper
"""
from app.simulation.engine_interface import JUNCTIONS, SCENARIOS, SimulationEngine
from app.simulation.junction_mapper import JunctionMapper
from app.simulation.simulated_engine import SimulatedEngine
from app.simulation.simulation_manager import SimulationManager
from app.simulation.sumo_engine import SumoEngine, sumo_available
from app.simulation.telemetry_collector import TelemetryCollector

# Shared alias for MockEngine as required by prompt
MockEngine = SimulatedEngine

__all__ = [
    "JUNCTIONS",
    "SCENARIOS",
    "SimulationEngine",
    "SumoEngine",
    "SimulatedEngine",
    "MockEngine",
    "SimulationManager",
    "TelemetryCollector",
    "JunctionMapper",
    "sumo_available",
]
