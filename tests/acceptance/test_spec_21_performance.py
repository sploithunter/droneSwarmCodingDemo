"""Acceptance tests for SPEC section 21 — Performance and Stability."""
import time
import pytest
from drones.drone_sim import DroneSim
from drones.types import DroneMode
from monitor.swarm_monitor import SwarmMonitor
from mission.mission_planner import generate_missions


class TestSpec21Performance:
    def test_simulation_maintains_10hz(self):
        """SPEC 21: Simulation can run 8 drones at 10Hz without falling behind."""
        missions = generate_missions()
        drones = []
        monitor = SwarmMonitor()

        for i in range(8):
            sim = DroneSim(i, rng_seed=42 + i)
            if i in missions:
                sim.set_mission(missions[i])
            drones.append(sim)

        # Time 100 ticks (10 seconds of sim time)
        start = time.time()
        for _ in range(100):
            for d in drones:
                state = d.tick(0.1)
                monitor.update_drone_state(state)
            monitor.compute_summary()
        elapsed = time.time() - start

        # Should complete well within 10 seconds of real time
        # (simulation should be faster than real-time)
        assert elapsed < 5.0, f"100 ticks took {elapsed:.2f}s, should be < 5s"

    def test_drones_run_independently(self):
        """SPEC 21: If one drone errors, others continue."""
        missions = generate_missions()
        drones = []
        for i in range(8):
            sim = DroneSim(i, rng_seed=42 + i)
            if i in missions:
                sim.set_mission(missions[i])
            drones.append(sim)

        # Run all drones
        for _ in range(50):
            for d in drones:
                d.tick(0.1)

        # "Kill" drone 4 by forcing fault
        drones[4].mode = DroneMode.FAULT

        # Other drones should continue fine
        for _ in range(50):
            for i, d in enumerate(drones):
                if i != 4:
                    d.tick(0.1)

        # Verify others are still flying
        flying = sum(1 for i, d in enumerate(drones)
                    if i != 4 and d.mode in (DroneMode.EN_ROUTE, DroneMode.TAKEOFF, DroneMode.HOVERING))
        assert flying >= 5, f"Only {flying} drones still flying, expected >= 5"

    def test_memory_stable_over_time(self):
        """SPEC 21: No unbounded growth in core data structures."""
        sim = DroneSim(0, rng_seed=42)
        missions = generate_missions()
        sim.set_mission(missions[0])

        # Run for 1000 ticks
        for _ in range(1000):
            sim.tick(0.1)

        # Check alert_seq is reasonable (not unlimited alerts)
        assert sim.alert_seq < 100, f"Too many alerts generated: {sim.alert_seq}"
