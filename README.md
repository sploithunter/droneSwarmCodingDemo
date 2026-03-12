# DDS Drone Swarm Monitoring System

A real-time drone swarm simulation and monitoring dashboard built with Python and React. Simulates 8 autonomous drones executing missions over a 2km x 2km operational area near Sunnyvale, CA, with live telemetry, fault injection, and command-and-control capabilities.

Built as a demonstration of agentic coding capabilities for RTI's DDS development team.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Python Backend                       │
│                                                     │
│  8 Drone Simulators ──→ Swarm Monitor               │
│    (flight physics,      (aggregation,              │
│     battery model,        1Hz summary)              │
│     fault injection)                                │
│         │                      │                    │
│         └──────┬───────────────┘                    │
│                ▼                                    │
│        WebSocket Bridge (5Hz batching)              │
│              port 8765                              │
└────────────────┬────────────────────────────────────┘
                 │ JSON over WebSocket
┌────────────────▼────────────────────────────────────┐
│              React Dashboard                         │
│                                                     │
│  Leaflet Map ─ Drone Markers, Trails, Geofence      │
│  Swarm Overview ─ Status Cards, Battery Stats        │
│  Alert Feed ─ Real-time fault/battery alerts         │
│  Telemetry Charts ─ Battery, Altitude, Speed,        │
│                      Motor RPM, Temperature          │
│  Command Panel ─ RTB, Hover, Resume, Emergency Land  │
│              port 5173 (dev)                         │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- `websockets` Python package (`pip install websockets`)

### Install

```bash
# Clone
git clone https://github.com/sploithunter/droneSwarmCodingDemo.git
cd droneSwarmCodingDemo

# Install Python dependencies
pip install websockets numpy

# Install dashboard dependencies
cd dashboard && npm install && cd ..
```

### Run

**Option 1: Launch script**
```bash
./scripts/start_all.sh
```

**Option 2: Manual (two terminals)**
```bash
# Terminal 1: Start simulation + WebSocket bridge
python -m drones.run_swarm

# Terminal 2: Start React dashboard
cd dashboard && npm run dev
```

Then open **http://localhost:5173** in your browser.

### Stop

```bash
./scripts/stop_all.sh
# or Ctrl+C in each terminal
```

## What You'll See

- **8 drone markers** moving across a Leaflet map around Sunnyvale, CA
- **7 active missions**: perimeter patrol, grid search (north/south), radial survey, diagonal cross, circle patrol, point inspection
- **Drone 7 (HOTEL)** stays idle at base until you command it
- **Faults** randomly injected: motor anomalies, GPS degradation, comm timeouts, critical faults
- **Battery drain** at realistic rates — CHARLIE (88% start) will trigger low-battery alerts first
- **Real-time telemetry** charts for the selected drone
- **Command panel** to send RTB, Hover, Resume, Emergency Land, Set Speed/Altitude, Go To Waypoint

## Drone Personalities

| ID | Callsign | Battery | Speed | Trait |
|----|----------|---------|-------|-------|
| 0 | ALPHA | 100% | 10 m/s | Reliable baseline |
| 1 | BRAVO | 95% | 12 m/s | Aggressive speed |
| 2 | CHARLIE | 88% | 10 m/s | Low battery start |
| 3 | DELTA | 100% | 10 m/s | GPS-prone (3x rate) |
| 4 | ECHO | 97% | 10 m/s | Motor-prone (3x rate) |
| 5 | FOXTROT | 100% | 8 m/s | Slow and steady |
| 6 | GOLF | 92% | 13 m/s | Fast, high drain |
| 7 | HOTEL | 100% | 10 m/s | Idle until commanded |

## Running Tests

```bash
# Python tests (313 tests)
python -m pytest tests/ -v

# Dashboard tests (57 tests)
cd dashboard && npm test
```

## Project Structure

```
├── drones/
│   ├── types.py            # DDS data types (enums + dataclasses)
│   ├── drone_config.py     # Per-drone personalities + physics constants
│   ├── flight_physics.py   # Kinematic model, waypoint following
│   ├── battery_model.py    # Battery drain + voltage + alerts
│   ├── fault_injector.py   # Probabilistic fault generation
│   ├── drone_sim.py        # Full state machine simulator
│   └── run_swarm.py        # Launcher for all 8 drones + monitor + bridge
├── mission/
│   ├── mission_patterns.py # 7 geometric flight patterns
│   └── mission_planner.py  # Mission assignment for drones 0-6
├── monitor/
│   └── swarm_monitor.py    # Aggregate stats → SwarmSummary
├── bridge/
│   └── ws_bridge.py        # DDS-to-WebSocket bridge (5Hz batching)
├── dashboard/
│   └── src/
│       ├── components/     # React UI components
│       ├── context/        # WebSocket state management
│       ├── hooks/          # useWebSocket, useDroneData
│       └── utils/          # Constants, geo utilities
├── tests/
│   ├── unit/               # 11 unit test files
│   └── acceptance/         # 12 acceptance test files (SPEC sections 1-21)
├── idl/                    # DDS IDL reference
├── qos/                    # QoS profile XML
├── scripts/                # Start/stop scripts
└── docs/                   # VISION.md, SPEC.md, PLAN.md
```

## Tech Stack

**Backend**: Python 3, asyncio, websockets
**Frontend**: React 18, Vite, Leaflet, Recharts
**Testing**: pytest (Python), Vitest + Testing Library (React)
**Designed for**: RTI Connext DDS (runs without it via try/except fallback)

## DDS Integration

The system is designed for RTI Connext DDS but runs standalone. When `rti.connextdds` is available:
- Each drone becomes a DDS DomainParticipant publishing DroneState/DroneAlert
- The bridge subscribes to all 5 DDS topics
- QoS profiles in `qos/USER_QOS_PROFILES.xml` configure reliability, durability, deadlines

Without DDS, everything runs in-process with direct function calls — same logic, same data flow.
