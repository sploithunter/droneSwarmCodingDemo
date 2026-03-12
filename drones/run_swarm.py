"""Swarm launcher — runs all 8 drones, monitor, and bridge in a single process."""
import asyncio
import signal
import sys
import time
import threading
import json

from drones.drone_sim import DroneSim
from drones.types import DroneMode
from monitor.swarm_monitor import SwarmMonitor
from bridge.ws_bridge import WebSocketBridge
from mission.mission_planner import generate_missions


class SwarmRunner:
    """Runs the full drone swarm simulation with WebSocket bridge."""

    def __init__(self):
        self.running = False
        self.drones = []
        self.monitor = None
        self.bridge = None
        self.missions = {}

    def setup(self):
        """Initialize all components."""
        # Create bridge
        self.bridge = WebSocketBridge(command_callback=self._handle_command)

        # Create monitor
        self.monitor = SwarmMonitor(
            total_drones=8,
            writer_callback=lambda s: self.bridge.on_summary(s)
        )

        # Create drones
        for drone_id in range(8):
            sim = DroneSim(
                drone_id=drone_id,
                writer_callback=lambda state, b=self.bridge: b.on_drone_state(state),
                alert_callback=lambda alert, b=self.bridge, m=self.monitor: (
                    b.on_alert(alert),
                    m.update_alert(alert),
                ),
            )
            self.drones.append(sim)

        # Generate and assign missions
        self.missions = generate_missions()
        for drone_id, mission in self.missions.items():
            self.drones[drone_id].set_mission(mission)
            self.bridge.on_mission(mission)

    def _handle_command(self, cmd):
        """Route a command from the bridge to the appropriate drone(s)."""
        for drone in self.drones:
            drone.handle_command(cmd)

    async def run(self):
        """Main async run loop."""
        self.running = True
        self.setup()

        # Start WebSocket server
        try:
            server = await self.bridge.start()
            print(f"WebSocket bridge listening on ws://0.0.0.0:8765")
        except Exception as e:
            print(f"Warning: Could not start WebSocket server: {e}")
            print("Running simulation without WebSocket bridge.")

        print(f"Starting swarm simulation with 8 drones...")
        print(f"Missions assigned to drones 0-6. Drone 7 (HOTEL) idle.")

        dt = 0.1  # 10 Hz
        monitor_interval = 1.0  # 1 Hz
        last_monitor_time = time.time()
        tick_count = 0

        try:
            while self.running:
                loop_start = time.time()

                # Tick all drones
                for drone in self.drones:
                    state = drone.tick(dt)
                    self.monitor.update_drone_state(state)

                # Compute and publish swarm summary at 1 Hz
                now = time.time()
                if now - last_monitor_time >= monitor_interval:
                    self.monitor.compute_summary()
                    last_monitor_time = now

                tick_count += 1
                if tick_count % 100 == 0:  # Every 10 seconds
                    self._print_status()

                # Sleep to maintain 10 Hz
                elapsed = time.time() - loop_start
                sleep_time = max(0, dt - elapsed)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            print("\nSwarm simulation stopped.")

    def _print_status(self):
        """Print a brief status line."""
        modes = {}
        for drone in self.drones:
            mode_name = DroneMode(drone.mode).name
            modes[mode_name] = modes.get(mode_name, 0) + 1
        batteries = [f"{d.battery.pct:.0f}%" for d in self.drones]
        print(f"  Modes: {modes} | Batteries: {', '.join(batteries)}")

    def stop(self):
        self.running = False


def main():
    runner = SwarmRunner()

    def signal_handler(sig, frame):
        print("\nShutting down...")
        runner.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
