"""Simulation Manager — Thread-safe manager owning active TraCI connection.

Key Design:
1. One SimulationManager that owns the active TraCI connection.
2. Prevents concurrent FastAPI request threads from directly calling TraCI.
3. Uses a controlled simulation worker task and thread-safe / async command queue.
4. Provides start, pause, resume, stop, reset, set_scenario, and step commands.
5. Emits telemetry updates through a callback or WebSocket broadcast.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Literal

from app.simulation.engine_interface import SimulationEngine
from app.simulation.simulated_engine import SimulatedEngine
from app.simulation.sumo_engine import SumoEngine, sumo_available

logger = logging.getLogger("simulation_manager")


@dataclass
class SimulationCommand:
    action: Literal["start", "pause", "resume", "stop", "reset", "scenario", "step", "status"]
    payload: dict[str, Any] = field(default_factory=dict)
    response_future: asyncio.Future = field(default_factory=asyncio.Future)


class SimulationManager:
    """Thread-safe and async coordinator for simulation lifecycle and TraCI safety."""

    def __init__(
        self,
        default_engine_type: Literal["simulated", "sumo"] = "simulated",
        gui: bool = False,
        telemetry_callback: Callable[[dict[str, Any]], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        self.engine_type = default_engine_type
        self.gui = gui
        self.telemetry_callback = telemetry_callback

        self.engine: SimulationEngine = self._create_engine(default_engine_type, gui=gui)
        self.command_queue: asyncio.Queue[SimulationCommand] = asyncio.Queue()
        self.worker_task: asyncio.Task | None = None
        self._running: bool = False
        self._paused: bool = True
        self._scenario: str = "normal"
        self._tick: int = 0
        self._lock = asyncio.Lock()
        self._latest_telemetry: dict[str, Any] = {}

    def _create_engine(self, engine_type: str, gui: bool = False) -> SimulationEngine:
        if engine_type == "sumo":
            ok, why = sumo_available()
            if not ok:
                raise RuntimeError(f"SUMO not available: {why}")
            return SumoEngine(gui=gui)
        return SimulatedEngine()

    async def start_worker(self) -> None:
        """Start the background worker processing commands and stepping simulation."""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker_loop())

    async def stop_worker(self) -> None:
        """Gracefully stop worker."""
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            self.worker_task = None
        if isinstance(self.engine, SumoEngine):
            self.engine.close()

    async def _worker_loop(self) -> None:
        """Controlled single-thread execution loop owning TraCI access."""
        logger.info("SimulationManager worker loop started.")
        while True:
            # 1. Process any pending commands in queue
            while not self.command_queue.empty():
                cmd = await self.command_queue.get()
                try:
                    res = await self._execute_command(cmd)
                    if not cmd.response_future.done():
                        cmd.response_future.set_result(res)
                except Exception as ex:
                    if not cmd.response_future.done():
                        cmd.response_future.set_exception(ex)
                finally:
                    self.command_queue.task_done()

            # 2. If running and not paused, advance 1 simulation step
            if self._running and not self._paused:
                try:
                    telemetry = self.engine.step()
                    self._tick = telemetry.get("tick", self._tick + 1)
                    self._latest_telemetry = telemetry

                    # Broadcast telemetry
                    if self.telemetry_callback:
                        try:
                            await self.telemetry_callback(telemetry)
                        except Exception as e:
                            logger.error("Telemetry callback failed: %s", e)
                except Exception as e:
                    logger.error("Simulation step failed: %s", e)
                    self._paused = True

            # Advance rate: 1 tick per second
            await asyncio.sleep(1.0)

    async def _execute_command(self, cmd: SimulationCommand) -> dict[str, Any]:
        """Execute simulation action exclusively within worker."""
        action = cmd.action
        payload = cmd.payload

        if action == "start":
            scenario = payload.get("scenario", self._scenario)
            target_engine = payload.get("engine", self.engine_type)
            gui = payload.get("gui", self.gui)

            # Switch engine if requested
            if target_engine != self.engine_type or (target_engine == "sumo" and gui != self.gui):
                if hasattr(self.engine, "close"):
                    self.engine.close()
                self.engine = self._create_engine(target_engine, gui=gui)
                self.engine_type = target_engine
                self.gui = gui

            res = self.engine.start(scenario=scenario)
            self._running = True
            self._paused = False
            self._scenario = scenario
            return {"status": "started", "engine_source": self.engine.source, **res}

        elif action == "pause":
            res = self.engine.pause()
            self._paused = True
            return {"status": "paused", **res}

        elif action == "resume":
            if not self._running:
                # If not yet started, start
                return await self._execute_command(SimulationCommand(action="start", payload=payload))
            self._paused = False
            self.engine.running = True
            return {"status": "resumed", **self.engine.status()}

        elif action == "stop":
            if hasattr(self.engine, "close"):
                self.engine.close()
            self._running = False
            self._paused = True
            return {"status": "stopped", **self.engine.status()}

        elif action == "reset":
            res = self.engine.reset()
            self._running = False
            self._paused = True
            self._tick = 0
            self._latest_telemetry = {}
            return {"status": "reset", **res}

        elif action == "scenario":
            scenario = payload.get("scenario", "normal")
            res = self.engine.set_scenario(scenario)
            self._scenario = scenario
            return {"status": "ok", **res}

        elif action == "step":
            telemetry = self.engine.step()
            self._tick = telemetry.get("tick", self._tick + 1)
            self._latest_telemetry = telemetry
            return telemetry

        elif action == "status":
            st = self.engine.status()
            return {
                **st,
                "manager_running": self._running,
                "manager_paused": self._paused,
                "manager_tick": self._tick,
                "latest_telemetry": self._latest_telemetry,
            }

        raise ValueError(f"Unknown command action: {action}")

    # Public thread-safe async dispatchers
    async def dispatch_command(self, action: str, payload: dict[str, Any] | None = None) -> Any:
        await self.start_worker()
        cmd = SimulationCommand(action=action, payload=payload or {})
        await self.command_queue.put(cmd)
        return await cmd.response_future

    async def start(self, scenario: str = "normal", engine: str = "sumo", gui: bool = False) -> dict[str, Any]:
        return await self.dispatch_command("start", {"scenario": scenario, "engine": engine, "gui": gui})

    async def pause(self) -> dict[str, Any]:
        return await self.dispatch_command("pause")

    async def resume(self) -> dict[str, Any]:
        return await self.dispatch_command("resume")

    async def stop(self) -> dict[str, Any]:
        return await self.dispatch_command("stop")

    async def reset(self) -> dict[str, Any]:
        return await self.dispatch_command("reset")

    async def set_scenario(self, scenario: str) -> dict[str, Any]:
        return await self.dispatch_command("scenario", {"scenario": scenario})

    async def step(self) -> dict[str, Any]:
        return await self.dispatch_command("step")

    async def get_status(self) -> dict[str, Any]:
        return await self.dispatch_command("status")
