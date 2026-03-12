# DDS Drone Swarm Monitoring System — Implementation Plan

## Context

Build a DDS-based drone swarm simulation (8 drones) with a real-time React dashboard, for a presentation to RTI's DDS dev team demonstrating agentic coding capabilities. The project is greenfield — only `docs/VISION.md` and `docs/SPEC.md` exist. Target ~10K lines across ~3 hours. The SPEC.md contains 120+ GWT acceptance scenarios that serve as both requirements and test gates.

**Testing philosophy**: Test early, test often. Nothing advances to the next phase until ALL unit tests, acceptance tests, and e2e tests pass. Failed tests are never skipped or deleted — the code is fixed instead.

**Project root**: `/Users/jason/Documents/swarmMonitor`

---

## Testing Frameworks

- **Python**: `pytest` + `pytest-asyncio`
- **React**: `vitest` + `@testing-library/react` + `jsdom`
- **DDS-dependent tests**: marked `@pytest.mark.skipif` when RTI runtime unavailable
- **Acceptance test naming**: `tests/acceptance/test_spec_NN_<topic>.py` (Python), `dashboard/src/__tests__/acceptance/specNN.test.jsx` (React)

---

## Phase 1: Foundation (~1,200 lines) ✅

### 1A — Project skeleton + DDS type definitions ✅
### 1B — QoS profiles XML ✅
### 1C — Drone configuration table ✅
### 1D — React project scaffold ✅

---

## Phase 2: Drone Simulation (~2,800 lines) ✅

### 2A — Flight physics engine ✅
### 2B — Battery model ✅
### 2C — Fault injector ✅
### 2D — Drone state machine (core simulator) ✅
### 2E — DDS integration for drone simulator (deferred — requires RTI runtime)
### 2F — Mission patterns and planner ✅
### 2G — Swarm monitor and launcher ✅

---

## Phase 3: WebSocket Bridge (~1,000 lines)

### 3A — WebSocket server with message protocol

**Create**: `bridge/ws_bridge.py`

- Async WebSocket server on port 8765
- DDS subscriber to all 5 topics
- DroneState batching at 5Hz → `drone_state_batch` messages
- Alert/Mission/Summary forwarded immediately
- Command relay: JSON → DroneCommand → DDS
- Multi-client broadcast, graceful disconnect handling
- JSON serialization of all DDS types

**Tests**:
- `tests/unit/test_ws_bridge.py` — JSON serialization, batch structure, command deserialization, throttle logic
- `tests/acceptance/test_spec_10_bridge.py` — SPEC section 10

---

## Phase 4: React Dashboard (~3,500 lines)

### 4A — WebSocket context and data hooks
### 4B — Header, connection status, dark mode
### 4C — Map panel
### 4D — Swarm overview + alert feed
### 4E — Drone selector
### 4F — Telemetry charts
### 4G — Command panel

---

## Phase 5: Integration & Polish (~1,500 lines)

### 5A — Launch scripts
### 5B — Python integration tests (requires RTI)
### 5C — E2E acceptance tests
### 5D — Dashboard e2e smoke test
### 5E — Polish

---

## SPEC Coverage Map

| SPEC | Test Files | Phase |
|------|-----------|-------|
| 1 (Types) | `test_types.py`, `test_spec_01_types.py` | 1A ✅ |
| 2 (QoS) | `test_qos_xml.py`, `test_spec_02_qos.py` | 1B ✅ |
| 3 (State Machine) | `test_drone_sim.py`, `test_spec_03_statemachine.py` | 2D ✅ |
| 4 (Physics) | `test_flight_physics.py`, `test_spec_04_physics.py` | 2A ✅ |
| 5 (Battery) | `test_battery_model.py`, `test_spec_05_battery.py` | 2B ✅ |
| 6 (Faults) | `test_fault_injector.py`, `test_spec_06_faults.py` | 2C ✅ |
| 7 (Personalities) | `test_drone_config.py`, `test_spec_07_personalities.py` | 1C ✅ |
| 8 (Missions) | `test_mission_patterns.py`, `test_spec_08_missions.py` | 2F ✅ |
| 9 (Summary) | `test_swarm_monitor.py`, `test_spec_09_summary.py` | 2G ✅ |
| 10 (Bridge) | `test_ws_bridge.py`, `test_spec_10_bridge.py` | 3A |
| 11 (Connection) | `spec11.test.jsx` | 4B |
| 12 (Map) | `spec12.test.jsx` | 4C |
| 13 (Overview) | `spec13.test.jsx` | 4D |
| 14 (Alerts) | `spec14.test.jsx` | 4D |
| 15 (Selector) | `spec15.test.jsx` | 4E |
| 16 (Charts) | `spec16.test.jsx` | 4F |
| 17 (Commands) | `spec17.test.jsx` | 4G |
| 18 (Dark Mode) | `spec18.test.jsx` | 4B |
| 19 (Data Mgmt) | `spec19.test.jsx` | 4A |
| 20 (E2E) | `test_spec_20_e2e.py`, `spec20_e2e.test.jsx` | 5C/5D |
| 21 (Performance) | `test_spec_21_performance.py` | 5C |
