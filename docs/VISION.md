# DDS Drone Swarm Monitoring System — Technical Vision Document

## Project Overview

Build a complete DDS-based drone swarm simulation and real-time monitoring dashboard. The system simulates 8 autonomous drones executing missions over a defined operational area, communicating entirely via RTI Connext DDS, with a React web dashboard providing real-time visualization and command-and-control capabilities.

The system has three layers:

1. **DDS Layer** — IDL-defined data types, QoS profiles, and the pub/sub topology
2. **Drone Simulation Layer** — 8 independent Python processes (one per drone), each a DDS participant
3. **Dashboard Layer** — A Python DDS-to-WebSocket bridge feeding a React/Recharts frontend

---

## 1. DDS Data Model (IDL)

### 1.1 Core Types

```idl
// ---- Enumerations ----

enum DroneMode {
    IDLE,
    TAKEOFF,
    EN_ROUTE,
    HOVERING,
    RETURNING_TO_BASE,
    LANDING,
    LANDED,
    FAULT
};

enum AlertSeverity {
    INFO,
    WARNING,
    CRITICAL
};

enum AlertType {
    LOW_BATTERY,
    GEOFENCE_BREACH,
    COLLISION_WARNING,
    MOTOR_FAULT,
    GPS_DEGRADED,
    COMMUNICATION_TIMEOUT,
    MISSION_COMPLETE
};

enum CommandType {
    GOTO_WAYPOINT,
    RETURN_TO_BASE,
    HOVER,
    RESUME_MISSION,
    EMERGENCY_LAND,
    SET_SPEED,
    SET_ALTITUDE
};

// ---- Coordinate Types ----

struct GeoPoint {
    double latitude;   // degrees, WGS84
    double longitude;  // degrees, WGS84
    float altitude_m;  // meters above ground level (AGL)
};

struct Vector3 {
    float x;  // m/s or m/s^2 depending on context
    float y;
    float z;
};

// ---- Primary Data Types ----

@topic
struct DroneState {
    @key
    uint8 drone_id;               // 0-7

    // Timestamp
    int64 timestamp_ns;            // nanoseconds since epoch

    // Position & motion
    GeoPoint position;
    float heading_deg;             // 0-360 compass heading
    Vector3 velocity;              // NED frame, m/s
    float ground_speed_mps;        // derived, m/s

    // Status
    DroneMode mode;
    float battery_pct;             // 0.0 - 100.0
    float battery_voltage;         // volts
    float signal_strength_dbm;     // RSSI

    // Mission progress
    uint16 current_waypoint_idx;
    uint16 total_waypoints;
    float mission_progress_pct;    // 0.0 - 100.0

    // Health indicators
    float motor_rpm[4];            // quadcopter, 4 motors
    float internal_temp_c;         // degrees celsius
    uint8 gps_satellite_count;
    float gps_hdop;                // horizontal dilution of precision
};

@topic
struct DroneCommand {
    @key
    uint8 drone_id;                // 0-7, or 255 for broadcast to all

    int64 timestamp_ns;
    CommandType command;

    // Payload (interpreted based on command type)
    GeoPoint target_position;      // for GOTO_WAYPOINT
    float parameter;               // speed for SET_SPEED, altitude for SET_ALTITUDE

    uint32 command_seq;            // monotonic sequence number for ack tracking
    string<128> issuer;            // "dashboard", "mission_planner", etc.
};

@topic
struct DroneAlert {
    @key
    uint8 drone_id;
    @key
    uint32 alert_seq;              // unique per drone

    int64 timestamp_ns;
    AlertType alert_type;
    AlertSeverity severity;
    string<256> message;

    // Context
    GeoPoint position;
    float battery_pct;
    DroneMode drone_mode;

    boolean acknowledged;
};

@topic
struct MissionPlan {
    @key
    uint8 drone_id;

    int64 timestamp_ns;
    uint16 waypoint_count;
    sequence<GeoPoint, 64> waypoints;
    float cruise_speed_mps;        // default cruise speed
    float cruise_altitude_m;       // default altitude

    boolean is_active;
    string<128> mission_name;
};

@topic
struct SwarmSummary {
    @key
    uint8 summary_id;              // always 0, singleton topic

    int64 timestamp_ns;
    uint8 total_drones;
    uint8 active_drones;
    uint8 faulted_drones;
    uint8 returning_drones;
    uint8 idle_drones;

    float avg_battery_pct;
    float min_battery_pct;
    uint8 min_battery_drone_id;

    float total_distance_covered_m;
    uint16 active_alerts;
    uint16 missions_completed;
};
```

### 1.2 Topic Names

| Topic Name | Type | Typical Rate | Description |
|---|---|---|---|
| `drone/state` | DroneState | 10 Hz per drone | Core telemetry |
| `drone/command` | DroneCommand | On demand | Operator commands |
| `drone/alert` | DroneAlert | Event-driven | System alerts |
| `drone/mission` | MissionPlan | On demand | Mission definitions |
| `swarm/summary` | SwarmSummary | 1 Hz | Aggregate swarm status |

---

## 2. QoS Profiles

Define these in a `USER_QOS_PROFILES.xml` file.

### 2.1 Telemetry Profile (DroneState)

```xml
<qos_profile name="TelemetryProfile">
    <datawriter_qos>
        <reliability><kind>BEST_EFFORT_RELIABILITY_QOS</kind></reliability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>1</depth>
        </history>
        <deadline><period><sec>0</sec><nanosec>200000000</nanosec></period></deadline>
        <liveliness>
            <kind>AUTOMATIC_LIVELINESS_QOS</kind>
            <lease_duration><sec>2</sec><nanosec>0</nanosec></lease_duration>
        </liveliness>
        <ownership><kind>EXCLUSIVE_OWNERSHIP_QOS</kind></ownership>
        <ownership_strength><value>100</value></ownership_strength>
    </datawriter_qos>
    <datareader_qos>
        <reliability><kind>BEST_EFFORT_RELIABILITY_QOS</kind></reliability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>1</depth>
        </history>
        <deadline><period><sec>0</sec><nanosec>200000000</nanosec></period></deadline>
        <liveliness>
            <kind>AUTOMATIC_LIVELINESS_QOS</kind>
            <lease_duration><sec>2</sec><nanosec>0</nanosec></lease_duration>
        </liveliness>
    </datareader_qos>
</qos_profile>
```

Rationale: High-frequency positional data. Losing a sample is acceptable — stale data is not. EXCLUSIVE ownership allows for potential redundant drone state publishers (hot standby pattern). Deadline of 200ms catches drones that stop publishing. Liveliness lease of 2s detects crashed processes.

### 2.2 Command Profile (DroneCommand)

```xml
<qos_profile name="CommandProfile">
    <datawriter_qos>
        <reliability>
            <kind>RELIABLE_RELIABILITY_QOS</kind>
            <max_blocking_time><sec>1</sec><nanosec>0</nanosec></max_blocking_time>
        </reliability>
        <history>
            <kind>KEEP_ALL_HISTORY_QOS</kind>
        </history>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
    </datawriter_qos>
    <datareader_qos>
        <reliability><kind>RELIABLE_RELIABILITY_QOS</kind></reliability>
        <history>
            <kind>KEEP_ALL_HISTORY_QOS</kind>
        </history>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
    </datareader_qos>
</qos_profile>
```

Rationale: Commands must be delivered reliably. TRANSIENT_LOCAL ensures a late-joining drone receives the most recent command. KEEP_ALL prevents command loss under burst conditions.

### 2.3 Alert Profile (DroneAlert)

```xml
<qos_profile name="AlertProfile">
    <datawriter_qos>
        <reliability><kind>RELIABLE_RELIABILITY_QOS</kind></reliability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>32</depth>
        </history>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
        <lifespan><duration><sec>300</sec><nanosec>0</nanosec></duration></lifespan>
    </datawriter_qos>
    <datareader_qos>
        <reliability><kind>RELIABLE_RELIABILITY_QOS</kind></reliability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>128</depth>
        </history>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
    </datareader_qos>
</qos_profile>
```

Rationale: Alerts are reliable but bounded. 5-minute lifespan prevents stale alert buildup. Reader keeps more history than writer to avoid missing alerts during transient disconnects.

### 2.4 Mission Profile (MissionPlan)

```xml
<qos_profile name="MissionProfile">
    <datawriter_qos>
        <reliability><kind>RELIABLE_RELIABILITY_QOS</kind></reliability>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>1</depth>
        </history>
    </datawriter_qos>
    <datareader_qos>
        <reliability><kind>RELIABLE_RELIABILITY_QOS</kind></reliability>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>1</depth>
        </history>
    </datareader_qos>
</qos_profile>
```

Rationale: Only the latest mission per drone matters. TRANSIENT_LOCAL so newly started drones pick up their assigned mission.

### 2.5 Swarm Summary Profile (SwarmSummary)

```xml
<qos_profile name="SwarmSummaryProfile">
    <datawriter_qos>
        <reliability><kind>RELIABLE_RELIABILITY_QOS</kind></reliability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>1</depth>
        </history>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
    </datawriter_qos>
    <datareader_qos>
        <reliability><kind>RELIABLE_RELIABILITY_QOS</kind></reliability>
        <history>
            <kind>KEEP_LAST_HISTORY_QOS</kind>
            <depth>1</depth>
        </history>
        <durability><kind>TRANSIENT_LOCAL_DURABILITY_QOS</kind></durability>
    </datareader_qos>
</qos_profile>
```

---

## 3. DDS Domain Architecture

### 3.1 Domain ID

Use **domain 0** for simplicity. All participants join the same domain.

### 3.2 Participants

| Participant | Count | Publishers | Subscribers |
|---|---|---|---|
| Drone Simulator | 8 (one per drone) | DroneState, DroneAlert | DroneCommand, MissionPlan |
| Mission Planner | 1 | MissionPlan, DroneCommand | DroneState |
| Swarm Monitor | 1 | SwarmSummary | DroneState, DroneAlert |
| Dashboard Bridge | 1 | DroneCommand (from UI) | All topics |

### 3.3 Participant Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DDS Domain 0                                   │
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         ┌──────────┐          │
│  │ Drone 0  │ │ Drone 1  │ │ Drone 2  │  ...    │ Drone 7  │          │
│  │          │ │          │ │          │         │          │          │
│  │ PUB:     │ │ PUB:     │ │ PUB:     │         │ PUB:     │          │
│  │  State   │ │  State   │ │  State   │         │  State   │          │
│  │  Alert   │ │  Alert   │ │  Alert   │         │  Alert   │          │
│  │ SUB:     │ │ SUB:     │ │ SUB:     │         │ SUB:     │          │
│  │  Command │ │  Command │ │  Command │         │  Command │          │
│  │  Mission │ │  Mission │ │  Mission │         │  Mission │          │
│  └──────────┘ └──────────┘ └──────────┘         └──────────┘          │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────────────┐  │
│  │ Mission Planner│  │ Swarm Monitor  │  │ Dashboard Bridge         │  │
│  │                │  │                │  │                          │  │
│  │ PUB:           │  │ PUB:           │  │ SUB: All topics          │  │
│  │  MissionPlan   │  │  SwarmSummary  │  │ PUB: DroneCommand        │  │
│  │  DroneCommand  │  │ SUB:           │  │                          │  │
│  │ SUB:           │  │  DroneState    │  │ WebSocket ←→ React UI    │  │
│  │  DroneState    │  │  DroneAlert    │  │                          │  │
│  └────────────────┘  └────────────────┘  └──────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Drone Simulation (Python)

### 4.1 Operational Area

Define a rectangular operational area centered around a realistic location. Use a coordinate system near RTI's Sunnyvale office for fun:

- **Center**: 37.3861° N, -122.0839° W (Sunnyvale, CA)
- **Operational area**: 2km x 2km box around center
- **Geofence**: The operational area boundary itself
- **Base station**: Center of the operational area

### 4.2 Drone Behavior Model

Each drone runs as an independent Python process with the following state machine:

```
IDLE → TAKEOFF → EN_ROUTE ←→ HOVERING → RETURNING_TO_BASE → LANDING → LANDED
                    ↓                           ↑
                  FAULT ──────────────────────→ (manual recovery via command)
```

#### State Transitions:

- **IDLE → TAKEOFF**: On receiving a MissionPlan
- **TAKEOFF → EN_ROUTE**: When altitude reaches cruise_altitude_m
- **EN_ROUTE → HOVERING**: On HOVER command, or when reaching a waypoint and waiting
- **EN_ROUTE → RETURNING_TO_BASE**: On RTB command, or battery < 20%
- **HOVERING → EN_ROUTE**: On RESUME_MISSION command
- **EN_ROUTE → FAULT**: Random fault injection (see 4.4), motor RPM anomaly, GPS degradation
- **FAULT → RETURNING_TO_BASE**: On manual recovery command (only if fault is non-critical)
- **RETURNING_TO_BASE → LANDING**: When within 10m of base station
- **LANDING → LANDED**: When altitude < 0.5m
- **LANDED → IDLE**: Automatic after landing

#### Flight Physics (simplified, NOT MavLink):

- **Max speed**: 15 m/s
- **Cruise speed**: 10 m/s (configurable per mission)
- **Max altitude**: 120m AGL
- **Ascent rate**: 3 m/s
- **Descent rate**: 2 m/s
- **Turn rate**: 45 deg/s
- **Acceleration**: 3 m/s^2
- **Position update**: Simple kinematic integration at 10Hz

Waypoint following uses a simple "fly toward waypoint" algorithm:
1. Calculate bearing to next waypoint
2. Adjust heading toward bearing at turn rate
3. Fly at cruise speed (or decelerate within 50m of waypoint)
4. Waypoint reached when within 5m horizontally and 2m vertically
5. Advance to next waypoint

### 4.3 Battery Model

- **Capacity**: 100% (abstract units)
- **Drain rate (hovering)**: 0.5% per minute
- **Drain rate (cruising)**: 1.0% per minute
- **Drain rate (at speed > 12 m/s)**: 1.5% per minute
- **Alerts**: WARNING at 30%, CRITICAL at 20%, forced RTB at 15%
- **Voltage model**: Linear from 16.8V (100%) to 13.2V (0%), with voltage sag under load

### 4.4 Fault Injection

To make the demo interesting, inject faults probabilistically:

- **Motor anomaly**: 2% chance per minute per drone. One motor RPM drops by 30-50%. Drone can still fly but publishes MOTOR_FAULT alert. Clears after 30-60 seconds.
- **GPS degradation**: 3% chance per minute. Satellite count drops to 3-5, HDOP increases. GPS_DEGRADED alert. Position starts drifting randomly by up to 2m. Clears after 20-40 seconds.
- **Communication timeout**: 1% chance per minute. Drone stops publishing for 3-5 seconds, then resumes. Swarm monitor detects via liveliness.
- **Critical fault**: 0.5% chance per minute. Drone enters FAULT mode, stops mission, hovers in place. Requires manual EMERGENCY_LAND or recovery command.

### 4.5 Per-Drone Initialization

Each drone starts with different characteristics to make the visualization interesting:

| Drone ID | Callsign | Start Battery | Personality |
|---|---|---|---|
| 0 | ALPHA | 100% | Reliable, follows missions perfectly |
| 1 | BRAVO | 95% | Slightly aggressive speed, drains battery faster |
| 2 | CHARLIE | 88% | Starts with lower battery, will need RTB sooner |
| 3 | DELTA | 100% | GPS-prone, higher chance of GPS degradation |
| 4 | ECHO | 97% | Motor-prone, higher chance of motor faults |
| 5 | FOXTROT | 100% | Slow and steady, 8 m/s cruise speed |
| 6 | GOLF | 92% | Fast, 13 m/s cruise speed, high battery drain |
| 7 | HOTEL | 100% | Reliable backup, starts IDLE until commanded |

### 4.6 Motor RPM Simulation

Each drone has 4 motors. Normal RPMs:
- **Hovering**: 4500-5000 RPM per motor (with slight random variation)
- **Cruising**: 5000-6000 RPM (proportional to speed)
- **Ascending**: 6000-7000 RPM
- **Descending**: 3500-4500 RPM

Add ±100 RPM Gaussian noise per update cycle to make the telemetry realistic.

### 4.7 Internal Temperature Model

- **Base**: 35°C on ground
- **Flight**: Rises 0.5°C per minute of flight, caps at 65°C
- **Cooling**: -1°C per minute when idle/landed
- **Warning threshold**: 55°C

---

## 5. Mission Planner (Python)

A separate process that:

1. On startup, generates pre-defined missions for drones 0-6 (drone 7 starts idle)
2. Publishes MissionPlan samples for each drone
3. Subscribes to DroneState to track mission progress
4. Can re-issue missions or modify waypoints via command line (optional, stretch goal)

### 5.1 Pre-defined Missions

Generate missions as geometric patterns within the operational area for visual appeal on the map:

| Drone | Mission Pattern | Waypoints | Description |
|---|---|---|---|
| 0 (ALPHA) | Perimeter patrol | 8 | Rectangle around the operational area boundary |
| 1 (BRAVO) | Grid search north | 12 | Lawn-mower pattern over the north half |
| 2 (CHARLIE) | Grid search south | 12 | Lawn-mower pattern over the south half |
| 3 (DELTA) | Radial survey | 8 | Star pattern from center outward |
| 4 (ECHO) | Diagonal cross | 6 | X pattern across the area |
| 5 (FOXTROT) | Circle patrol | 16 | Large circle around the area |
| 6 (GOLF) | Point inspection | 4 | Direct flights between 4 distant points |
| 7 (HOTEL) | None (idle) | 0 | Waiting for dashboard commands |

All missions loop: when the last waypoint is reached, the drone returns to the first waypoint and repeats.

---

## 6. Swarm Monitor (Python)

A process that subscribes to DroneState (all 8 drones) and DroneAlert, computes aggregate statistics, and publishes SwarmSummary at 1 Hz.

Computed fields:
- Count drones by mode (active = EN_ROUTE or HOVERING, faulted = FAULT, returning = RTB, idle = IDLE or LANDED)
- Average and minimum battery across all active drones
- Accumulate total distance covered (sum of distance deltas per state update)
- Count active (unacknowledged) alerts
- Count completed missions (when a drone finishes all waypoints)

---

## 7. Dashboard Bridge (Python)

### 7.1 Architecture

A Python process that:
1. Creates a DDS DomainParticipant subscribing to ALL topics
2. Runs an `asyncio` WebSocket server (use `websockets` library) on port 8765
3. On each DDS sample received, serializes it to JSON and broadcasts to all connected WebSocket clients
4. Accepts JSON commands from WebSocket clients and publishes them as DroneCommand samples

### 7.2 WebSocket Message Protocol

All messages are JSON with a `type` field:

```json
// Server → Client (DDS data forwarded to dashboard)
{ "type": "drone_state", "data": { ... } }
{ "type": "drone_alert", "data": { ... } }
{ "type": "mission_plan", "data": { ... } }
{ "type": "swarm_summary", "data": { ... } }

// Client → Server (dashboard commands)
{
    "type": "drone_command",
    "data": {
        "drone_id": 3,
        "command": "RETURN_TO_BASE",
        "target_position": null,
        "parameter": 0.0
    }
}
```

### 7.3 Throttling

DroneState arrives at 10 Hz * 8 drones = 80 messages/sec. To avoid overwhelming the browser:
- Batch DroneState updates and send at most 5 Hz to the WebSocket
- Send other topic messages immediately (they are lower frequency)
- Include all 8 drones in each batched update message:

```json
{
    "type": "drone_state_batch",
    "timestamp_ns": 1234567890,
    "drones": [ { "drone_id": 0, ... }, { "drone_id": 1, ... }, ... ]
}
```

---

## 8. React Dashboard

### 8.1 Technology Stack

- **React 18** with functional components and hooks
- **Recharts** for time-series charts
- **Leaflet** (react-leaflet) for the 2D map with OpenStreetMap tiles
- **WebSocket** via native browser API (no library needed)
- CSS modules or Tailwind for styling
- **Vite** for build tooling

### 8.2 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  DRONE SWARM MONITOR         [Connected ●]    [Dark Mode Toggle]   │
├───────────────────────────────────────┬─────────────────────────────┤
│                                       │  Swarm Overview             │
│                                       │  ┌───┐ ┌───┐ ┌───┐ ┌───┐  │
│           Leaflet Map                 │  │ 6 │ │ 1 │ │ 0 │ │ 1 │  │
│                                       │  │ACT│ │FLT│ │RTB│ │IDL│  │
│    (drone markers with trails,        │  └───┘ └───┘ └───┘ └───┘  │
│     geofence boundary,                │                             │
│     waypoint paths,                   │  Avg Battery: 72%  ████░░  │
│     base station marker)              │  Min Battery: 31% (CHARLIE)│
│                                       │  Missions Done: 3          │
│                                       │  Active Alerts: 2          │
│                                       ├─────────────────────────────┤
│                                       │  Alert Feed                 │
│                                       │  ┌─────────────────────────┐│
│                                       │  │⚠ CHARLIE: Low battery  ││
│                                       │  │  31% - RTB initiated    ││
│                                       │  │● ECHO: Motor fault      ││
│                                       │  │  Motor 2 RPM degraded   ││
│                                       │  │○ DELTA: GPS degraded    ││
│                                       │  │  HDOP: 4.2, 4 sats     ││
│                                       │  └─────────────────────────┘│
├───────────────────────────────────────┼─────────────────────────────┤
│  Drone Selector: [0][1][2][3][4][5][6][7]    Selected: ALPHA (0)   │
├───────────────────────────────────────┬─────────────────────────────┤
│  Telemetry Charts (selected drone)    │  Command Panel              │
│                                       │                             │
│  Battery ──────────────\              │  [Go To Waypoint]           │
│  100%                   \──── 72%     │  Lat: [______] Lon: [_____]│
│                                       │  Alt: [______]             │
│  Altitude ────/\────/\────            │                             │
│  120m        /  \  /  \               │  [Return to Base]          │
│             /    \/    \──            │  [Hover]                   │
│                                       │  [Resume Mission]          │
│  Speed ─────/──\──/──\───            │  [Emergency Land]          │
│  15 m/s    /    \/    \               │                             │
│                                       │  [Set Speed] [____] m/s   │
│  Motor RPMs ──── (4 lines)            │  [Set Altitude] [____] m  │
│                                       │                             │
│  Temperature ─────/─────────          │  [Send to All Drones]     │
│  65°C                                 │                             │
└───────────────────────────────────────┴─────────────────────────────┘
```

### 8.3 Component Hierarchy

```
App
├── Header
│   ├── ConnectionStatus (WebSocket state indicator)
│   └── ThemeToggle
├── MainLayout
│   ├── MapPanel
│   │   ├── LeafletMap
│   │   │   ├── DroneMarker (x8, rotated icon showing heading)
│   │   │   ├── DroneTrail (x8, last 60 seconds of positions as polyline)
│   │   │   ├── WaypointPath (x8, mission waypoints as dashed lines)
│   │   │   ├── GeofenceBoundary (rectangle overlay)
│   │   │   └── BaseStationMarker
│   │   └── MapControls (zoom to fit, toggle trails, toggle waypoints)
│   └── SidePanel
│       ├── SwarmOverview
│       │   ├── StatusCards (active/faulted/returning/idle counts)
│       │   ├── BatteryOverview (avg, min with drone ID)
│       │   └── MissionStats
│       └── AlertFeed
│           └── AlertItem (severity icon, drone name, message, timestamp)
├── DroneSelector (clickable tabs for each drone, color-coded by status)
├── DetailLayout
│   ├── TelemetryPanel
│   │   ├── BatteryChart (line, 2-minute rolling window)
│   │   ├── AltitudeChart (line, 2-minute rolling window)
│   │   ├── SpeedChart (line, 2-minute rolling window)
│   │   ├── MotorRPMChart (4 lines overlaid, 30-second window)
│   │   └── TemperatureChart (line, 5-minute rolling window)
│   └── CommandPanel
│       ├── WaypointCommand (lat/lon/alt inputs + send)
│       ├── QuickCommands (RTB, Hover, Resume, E-Land buttons)
│       ├── ParameterCommands (speed/altitude sliders + send)
│       └── BroadcastToggle (send to selected vs all)
└── WebSocketProvider (context providing connection + data state)
```

### 8.4 State Management

Use React Context + useReducer for global state:

```typescript
interface AppState {
    // Connection
    wsConnected: boolean;

    // Live drone data (latest sample per drone)
    droneStates: Map<number, DroneState>;    // keyed by drone_id

    // Historical data for charts (ring buffers)
    droneHistory: Map<number, DroneStateHistory>;  // last 120 seconds

    // Trails for map (last 60 seconds of positions)
    droneTrails: Map<number, GeoPoint[]>;

    // Missions
    missions: Map<number, MissionPlan>;

    // Alerts (last 100)
    alerts: DroneAlert[];

    // Swarm summary
    swarmSummary: SwarmSummary | null;

    // UI state
    selectedDroneId: number;
    showTrails: boolean;
    showWaypoints: boolean;
    darkMode: boolean;
}
```

### 8.5 Map Visualization Details

- **Drone markers**: Custom SVG icons shaped like small quadcopters, rotated to match heading. Color-coded by mode:
  - EN_ROUTE: blue
  - HOVERING: cyan
  - RETURNING_TO_BASE: orange
  - FAULT: red (pulsing)
  - IDLE/LANDED: gray
- **Trails**: Semi-transparent polylines fading over 60 seconds (older points more transparent)
- **Waypoint paths**: Dashed lines connecting mission waypoints, with small circle markers at each waypoint. Active waypoint highlighted.
- **Geofence**: Red dashed rectangle overlay showing operational boundary
- **Base station**: Distinctive marker (house or helipad icon) at center

### 8.6 Chart Configuration

All charts use Recharts with the following shared config:
- Rolling time window (configurable: 30s, 1m, 2m, 5m)
- Responsive container
- Smooth animations disabled (real-time data, animations cause lag)
- Grid lines on both axes
- Units on Y-axis labels

### 8.7 Color Palette

| Element | Light Mode | Dark Mode |
|---|---|---|
| Background | #FFFFFF | #1A1A2E |
| Card background | #F5F5F5 | #16213E |
| Primary text | #333333 | #E0E0E0 |
| Accent | #2196F3 | #4FC3F7 |
| Success | #4CAF50 | #66BB6A |
| Warning | #FF9800 | #FFA726 |
| Danger | #F44336 | #EF5350 |
| Chart line 1 | #2196F3 | #4FC3F7 |
| Chart line 2 | #FF9800 | #FFA726 |
| Chart line 3 | #4CAF50 | #66BB6A |
| Chart line 4 | #9C27B0 | #CE93D8 |

---

## 9. Project File Structure

```
drone-swarm-dds/
├── README.md
├── idl/
│   └── DroneSwarm.idl           # All type definitions
├── qos/
│   └── USER_QOS_PROFILES.xml    # QoS profile definitions
├── drones/
│   ├── drone_sim.py             # Main drone simulator (parameterized by drone_id)
│   ├── flight_physics.py        # Kinematic model, waypoint following
│   ├── battery_model.py         # Battery drain simulation
│   ├── fault_injector.py        # Random fault generation
│   ├── drone_config.py          # Per-drone personality table
│   └── run_swarm.py             # Launcher: starts all 8 drones as subprocesses
├── mission/
│   ├── mission_planner.py       # Mission generation and publishing
│   └── mission_patterns.py      # Geometric pattern generators
├── monitor/
│   └── swarm_monitor.py         # Aggregate stats publisher
├── bridge/
│   └── ws_bridge.py             # DDS subscriber → WebSocket server
├── dashboard/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── context/
│   │   │   └── WebSocketContext.jsx
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── MapPanel.jsx
│   │   │   ├── DroneMarker.jsx
│   │   │   ├── SwarmOverview.jsx
│   │   │   ├── AlertFeed.jsx
│   │   │   ├── DroneSelector.jsx
│   │   │   ├── TelemetryPanel.jsx
│   │   │   ├── CommandPanel.jsx
│   │   │   └── charts/
│   │   │       ├── BatteryChart.jsx
│   │   │       ├── AltitudeChart.jsx
│   │   │       ├── SpeedChart.jsx
│   │   │       ├── MotorRPMChart.jsx
│   │   │       └── TemperatureChart.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js
│   │   │   └── useDroneData.js
│   │   ├── utils/
│   │   │   ├── constants.js
│   │   │   └── geo.js
│   │   └── styles/
│   │       └── theme.css
│   └── public/
│       └── drone-icon.svg
└── scripts/
    ├── start_all.sh             # Start everything: drones, planner, monitor, bridge, dashboard
    └── stop_all.sh              # Kill all processes
```

---

## 10. Startup Sequence

```bash
# Terminal 1: Start all DDS processes
./scripts/start_all.sh

# This runs (in order, with 2-second delays between each):
# 1. Swarm Monitor (needs to be up to catch early data)
# 2. Dashboard Bridge (WebSocket server)
# 3. Mission Planner (publishes missions)
# 4. Drone simulators 0-7 (start flying)

# Terminal 2: Start React dashboard
cd dashboard && npm run dev
# Open http://localhost:5173
```

---

## 11. Implementation Notes for Claude Code

### 11.1 Connext Python API

Use `rti.connextdds` Python package. Key patterns:

```python
import rti.connextdds as dds
import rti.types as idl

# Define types using @idl.struct decorator (alternative to IDL compilation)
@idl.struct
class GeoPoint:
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: idl.float32 = 0.0

@idl.struct(member_annotations={'drone_id': [idl.key]})
class DroneState:
    drone_id: idl.uint8 = 0
    # ... etc

# Create participant
participant = dds.DomainParticipant(domain_id=0)

# Create topic
topic = dds.Topic(participant, "drone/state", DroneState)

# QoS from XML
qos_provider = dds.QosProvider("qos/USER_QOS_PROFILES.xml")
writer_qos = qos_provider.datawriter_qos_from_profile("TelemetryProfile")

# Create writer
publisher = dds.Publisher(participant)
writer = dds.DataWriter(publisher, topic, qos=writer_qos)

# Write data
state = DroneState(drone_id=0, ...)
writer.write(state)
```

### 11.2 Python Dependencies

```
rti.connextdds          # RTI Connext DDS Python API
websockets              # Async WebSocket server
asyncio                 # Async runtime (stdlib)
numpy                   # Math for flight physics (optional but nice)
```

### 11.3 React Dependencies

```json
{
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-leaflet": "^4.2.1",
        "leaflet": "^1.9.4",
        "recharts": "^2.8.0"
    },
    "devDependencies": {
        "vite": "^5.0.0",
        "@vitejs/plugin-react": "^4.2.0"
    }
}
```

### 11.4 Key Implementation Priorities

If running low on time, prioritize in this order:

1. **DDS types and QoS profiles** — Foundation, get this right first
2. **One working drone simulator** — Get a single drone publishing state
3. **WebSocket bridge** — Get data flowing to the browser
4. **Map with drone markers** — Immediately visual and impressive
5. **All 8 drones with missions** — Full swarm simulation
6. **Swarm overview panel** — Aggregate stats
7. **Alert feed** — Event-driven UI updates
8. **Telemetry charts** — Per-drone detail views
9. **Command panel** — Interactive control from dashboard
10. **Dark mode, polish, fault injection tuning** — Nice-to-haves

### 11.5 Testing the System

To verify everything works without the full dashboard:

```bash
# In one terminal, run a single drone
python drones/drone_sim.py --drone-id 0

# In another terminal, subscribe to see the data
python -c "
import rti.connextdds as dds
import rti.types as idl
# ... quick subscriber to print DroneState samples
"
```

---

## 12. Presentation Narrative Arc

For the 40-minute presentation tomorrow, structure the story as:

1. **The Challenge** (2 min): "I needed to build a complex distributed system in one evening"
2. **The Spec** (3 min): Show this document. "I wrote a detailed vision doc and handed it to Claude Code"
3. **The Build** (20 min): Walk through the implementation session
   - Show key moments where the agent made good architectural decisions
   - Show moments where you had to course-correct
   - Show the iterative refinement process
   - Highlight how the agent handled DDS-specific concepts
4. **The Demo** (10 min): Run the system live
   - Start the swarm, show drones on the map
   - Show real-time telemetry updating
   - Send commands from the dashboard
   - Trigger a fault and show the alert system
5. **Lessons Learned** (5 min): What works, what doesn't, when to use agentic coding
