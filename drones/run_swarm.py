"""Swarm launcher — runs all 8 drones, monitor, and bridge.

Each drone gets its own DDS DomainParticipant (per VISION.md Section 3.2).
The monitor and bridge each get their own participants as well.
All communication flows through DDS on Domain 0.
"""
import asyncio
import signal
import time

from drones.drone_sim import DroneSim
from drones.types import DroneMode, _has_rti
from monitor.swarm_monitor import SwarmMonitor
from bridge.ws_bridge import WebSocketBridge
from mission.mission_planner import generate_missions


class SwarmRunner:
    """Runs the full drone swarm simulation with proper DDS architecture."""

    def __init__(self):
        self.running = False
        self.drones = []
        self.drone_dds = []  # One DroneParticipant per drone
        self.monitor = None
        self.monitor_dds = None  # MonitorParticipant
        self.bridge = None
        self.bridge_dds = None  # BridgeParticipant
        self.missions = {}

    def setup(self):
        """Initialize all components with proper DDS architecture."""
        dds_enabled = False

        if _has_rti:
            try:
                from drones.dds_manager import (
                    DroneParticipant, MonitorParticipant, BridgeParticipant
                )

                # Each drone gets its own DomainParticipant
                for drone_id in range(8):
                    dp = DroneParticipant(drone_id=drone_id, domain_id=0)
                    self.drone_dds.append(dp)

                # Monitor gets its own DomainParticipant
                self.monitor_dds = MonitorParticipant(domain_id=0)

                # Bridge gets its own DomainParticipant
                self.bridge_dds = BridgeParticipant(domain_id=0)

                dds_enabled = True
                print("DDS ENABLED — 10 DomainParticipants on Domain 0:")
                print("  8x DroneParticipant  (PUB: DroneState, DroneAlert)")
                print("  1x MonitorParticipant (SUB: DroneState, DroneAlert; PUB: SwarmSummary)")
                print("  1x BridgeParticipant  (SUB: All topics; PUB: DroneCommand, MissionPlan)")
                print("  Run '$NDDSHOME/bin/rtiddsspy -printSample' to see DDS traffic")

            except Exception as e:
                dds_enabled = False
                self.drone_dds = []
                self.monitor_dds = None
                self.bridge_dds = None
                print(f"DDS initialization failed: {e}")
                import traceback
                traceback.print_exc()
                print("Falling back to local-only mode.")
        else:
            print("RTI Connext DDS not available — running in local-only mode.")

        # Create WebSocket bridge (always needed for dashboard)
        self.bridge = WebSocketBridge(command_callback=self._handle_command)

        # Create monitor
        self.monitor = SwarmMonitor(
            total_drones=8,
            writer_callback=self._on_summary
        )

        # Create drones — each with DDS-aware callbacks
        for drone_id in range(8):
            sim = DroneSim(
                drone_id=drone_id,
                writer_callback=self._make_state_callback(drone_id, dds_enabled),
                alert_callback=self._make_alert_callback(drone_id, dds_enabled),
            )
            self.drones.append(sim)

        # Generate and assign missions
        self.missions = generate_missions()
        for drone_id, mission in self.missions.items():
            self.drones[drone_id].set_mission(mission)
            # Publish missions via DDS (bridge acts as mission planner)
            if self.bridge_dds:
                self.bridge_dds.write_mission(mission)
            # Also forward to WebSocket bridge directly for non-DDS path
            self.bridge.on_mission(mission)

    def _make_state_callback(self, drone_id, dds_enabled):
        """Create a state callback for a specific drone."""
        def callback(state):
            # Publish via this drone's own DDS participant
            if dds_enabled and drone_id < len(self.drone_dds):
                self.drone_dds[drone_id].write_state(state)
            # Also forward to WebSocket bridge directly
            self.bridge.on_drone_state(state)
            # Update monitor in-process (monitor also reads from DDS)
            self.monitor.update_drone_state(state)
        return callback

    def _make_alert_callback(self, drone_id, dds_enabled):
        """Create an alert callback for a specific drone."""
        def callback(alert):
            # Publish via this drone's own DDS participant
            if dds_enabled and drone_id < len(self.drone_dds):
                self.drone_dds[drone_id].write_alert(alert)
            # Forward to WebSocket bridge and monitor
            self.bridge.on_alert(alert)
            self.monitor.update_alert(alert)
        return callback

    def _on_summary(self, summary):
        """Called by monitor — publish summary via DDS and forward to bridge."""
        if self.monitor_dds:
            self.monitor_dds.write_summary(summary)
        self.bridge.on_summary(summary)

    def _handle_command(self, cmd):
        """Route command from WebSocket — publish via DDS and handle locally."""
        # Publish command via DDS (bridge participant)
        if self.bridge_dds:
            self.bridge_dds.write_command(cmd)
        # Also route directly to drones (for immediate response)
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
                    drone.tick(dt)

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
            # Close all DDS participants
            for dp in self.drone_dds:
                dp.close()
            if self.monitor_dds:
                self.monitor_dds.close()
            if self.bridge_dds:
                self.bridge_dds.close()
            if self.drone_dds:
                print(f"Closed {len(self.drone_dds) + 2} DDS participants.")
            print("\nSwarm simulation stopped.")

    def _print_status(self):
        """Print a brief status line."""
        modes = {}
        for drone in self.drones:
            mode_name = DroneMode(drone.mode).name
            modes[mode_name] = modes.get(mode_name, 0) + 1
        batteries = [f"{d.battery.pct:.0f}%" for d in self.drones]
        dds_tag = f"DDS:{len(self.drone_dds)}+2" if self.drone_dds else "DDS:OFF"
        print(f"  [{dds_tag}] Modes: {modes} | Batteries: {', '.join(batteries)}")

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
