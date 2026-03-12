# DDS Drone Swarm Monitoring System — Acceptance Specification

All acceptance criteria are expressed in Given/When/Then format.
Each scenario serves as both a functional requirement and a verifiable acceptance test.

---

## 1. DDS Data Model

### 1.1 Type Definitions

```
Scenario: All IDL types are defined and usable
  Given the rti.connextdds Python package is available
  When I import the drone swarm type definitions module
  Then the following types are importable and instantiable:
    | Type           |
    | GeoPoint       |
    | Vector3        |
    | DroneState     |
    | DroneCommand   |
    | DroneAlert     |
    | MissionPlan    |
    | SwarmSummary   |
  And each type can be round-tripped through DDS serialization without data loss
```

```
Scenario: DroneState key field is drone_id
  Given a DroneState instance with drone_id = 3
  When I write it to the "drone/state" topic
  Then the sample is keyed by drone_id
  And a second write with drone_id = 3 updates the same instance
  And a write with drone_id = 4 creates a separate instance
```

```
Scenario: DroneAlert has composite key
  Given a DroneAlert instance with drone_id = 2 and alert_seq = 5
  When I write it to the "drone/alert" topic
  Then the sample is keyed by the combination of drone_id and alert_seq
  And a different alert_seq for the same drone_id creates a new instance
```

```
Scenario: Enum values map correctly
  Given the DroneMode enumeration
  Then it contains exactly these values in order:
    | IDLE | TAKEOFF | EN_ROUTE | HOVERING | RETURNING_TO_BASE | LANDING | LANDED | FAULT |
  And AlertSeverity contains: | INFO | WARNING | CRITICAL |
  And AlertType contains:
    | LOW_BATTERY | GEOFENCE_BREACH | COLLISION_WARNING | MOTOR_FAULT | GPS_DEGRADED | COMMUNICATION_TIMEOUT | MISSION_COMPLETE |
  And CommandType contains:
    | GOTO_WAYPOINT | RETURN_TO_BASE | HOVER | RESUME_MISSION | EMERGENCY_LAND | SET_SPEED | SET_ALTITUDE |
```

### 1.2 Topics

```
Scenario: All topics are discoverable on the domain
  Given a DDS DomainParticipant on domain 0
  When all system processes are running
  Then the following topics exist on the domain:
    | Topic Name       | Type         | Key Field(s)          |
    | drone/state      | DroneState   | drone_id              |
    | drone/command    | DroneCommand | drone_id              |
    | drone/alert      | DroneAlert   | drone_id, alert_seq   |
    | drone/mission    | MissionPlan  | drone_id              |
    | swarm/summary    | SwarmSummary | summary_id            |
```

---

## 2. QoS Profiles

### 2.1 QoS Profile File

```
Scenario: QoS profiles are loadable from XML
  Given the file qos/USER_QOS_PROFILES.xml exists
  When I create a QosProvider from that file
  Then the following profiles are available:
    | Profile Name         |
    | TelemetryProfile     |
    | CommandProfile       |
    | AlertProfile         |
    | MissionProfile       |
    | SwarmSummaryProfile  |
```

### 2.2 Telemetry QoS

```
Scenario: Telemetry uses best-effort reliability
  Given the TelemetryProfile QoS
  When I inspect the datawriter and datareader QoS
  Then reliability kind is BEST_EFFORT
  And history kind is KEEP_LAST with depth 1
  And deadline period is 200 milliseconds
  And liveliness kind is AUTOMATIC with lease duration 2 seconds
  And ownership kind is EXCLUSIVE with writer strength 100
```

### 2.3 Command QoS

```
Scenario: Commands use reliable delivery with durability
  Given the CommandProfile QoS
  When I inspect the datawriter and datareader QoS
  Then reliability kind is RELIABLE with max blocking time 1 second
  And history kind is KEEP_ALL
  And durability kind is TRANSIENT_LOCAL
```

### 2.4 Alert QoS

```
Scenario: Alerts are reliable with bounded history and lifespan
  Given the AlertProfile QoS
  When I inspect the datawriter QoS
  Then reliability kind is RELIABLE
  And history kind is KEEP_LAST with depth 32
  And durability kind is TRANSIENT_LOCAL
  And lifespan duration is 300 seconds
  When I inspect the datareader QoS
  Then history kind is KEEP_LAST with depth 128
```

### 2.5 Mission and Summary QoS

```
Scenario: Mission and summary profiles keep latest instance reliably
  Given the MissionProfile and SwarmSummaryProfile QoS
  When I inspect both profiles
  Then reliability kind is RELIABLE
  And durability kind is TRANSIENT_LOCAL
  And history kind is KEEP_LAST with depth 1
```

---

## 3. Drone Simulation — State Machine

### 3.1 Startup

```
Scenario: Drone starts in IDLE mode
  Given a drone simulator is launched with drone_id = 0
  When the process initializes
  Then the drone's mode is IDLE
  And it publishes DroneState at 10 Hz
  And its position is the base station location (37.3861, -122.0839)
  And its altitude is 0.0 meters
```

### 3.2 Mission Activation

```
Scenario: Drone transitions from IDLE to TAKEOFF on receiving a mission
  Given a drone in IDLE mode
  When a MissionPlan is published for that drone's drone_id with is_active = true
  Then the drone transitions to TAKEOFF mode
  And it begins ascending at 3 m/s
  And its motor RPMs increase to the ascending range (6000-7000)
```

```
Scenario: Drone transitions from TAKEOFF to EN_ROUTE at cruise altitude
  Given a drone in TAKEOFF mode with cruise_altitude_m = 50
  When the drone's altitude reaches 50 meters
  Then the drone transitions to EN_ROUTE mode
  And it begins navigating toward the first waypoint
  And its ground speed increases toward cruise speed
```

### 3.3 Waypoint Navigation

```
Scenario: Drone follows waypoints in sequence
  Given a drone in EN_ROUTE mode with 8 waypoints
  And the drone is heading toward waypoint index 0
  When the drone arrives within 5 meters horizontally and 2 meters vertically of waypoint 0
  Then current_waypoint_idx advances to 1
  And the drone adjusts heading toward waypoint 1
  And mission_progress_pct reflects (1/8) * 100 = 12.5%
```

```
Scenario: Drone decelerates when approaching a waypoint
  Given a drone in EN_ROUTE mode cruising at 10 m/s
  When the drone is within 50 meters of the next waypoint
  Then the drone begins decelerating
  And ground_speed_mps decreases as it approaches the waypoint
```

```
Scenario: Mission loops after completing all waypoints
  Given a drone in EN_ROUTE mode at waypoint index 7 of 8 total waypoints
  When the drone reaches the final waypoint
  Then current_waypoint_idx resets to 0
  And the drone navigates back toward waypoint 0
  And a MISSION_COMPLETE alert is published with severity INFO
```

### 3.4 Command Handling

```
Scenario: HOVER command pauses mission
  Given a drone in EN_ROUTE mode
  When a DroneCommand with command = HOVER is received for that drone
  Then the drone transitions to HOVERING mode
  And ground_speed_mps decreases to 0
  And the drone maintains its current position and altitude
  And current_waypoint_idx is preserved
```

```
Scenario: RESUME_MISSION resumes from hover
  Given a drone in HOVERING mode with current_waypoint_idx = 3
  When a DroneCommand with command = RESUME_MISSION is received
  Then the drone transitions to EN_ROUTE mode
  And it resumes navigating toward waypoint 3
```

```
Scenario: RETURN_TO_BASE command initiates return
  Given a drone in EN_ROUTE mode at position (37.390, -122.080)
  When a DroneCommand with command = RETURN_TO_BASE is received
  Then the drone transitions to RETURNING_TO_BASE mode
  And it navigates toward the base station (37.3861, -122.0839)
```

```
Scenario: GOTO_WAYPOINT sends drone to arbitrary location
  Given a drone in EN_ROUTE or HOVERING mode
  When a DroneCommand with command = GOTO_WAYPOINT and target_position = (37.388, -122.085, 60.0) is received
  Then the drone navigates toward the specified position
  And it maintains the specified altitude of 60 meters
```

```
Scenario: EMERGENCY_LAND initiates immediate landing
  Given a drone in any flight mode (TAKEOFF, EN_ROUTE, HOVERING, RETURNING_TO_BASE, FAULT)
  When a DroneCommand with command = EMERGENCY_LAND is received
  Then the drone transitions to LANDING mode
  And it begins descending at 2 m/s
  And it maintains its current horizontal position
```

```
Scenario: SET_SPEED adjusts cruise speed
  Given a drone in EN_ROUTE mode at cruise speed 10 m/s
  When a DroneCommand with command = SET_SPEED and parameter = 13.0 is received
  Then the drone adjusts its cruise speed to 13.0 m/s
  And ground_speed_mps changes to reflect the new target
```

```
Scenario: SET_ALTITUDE adjusts cruise altitude
  Given a drone in EN_ROUTE mode at altitude 50m
  When a DroneCommand with command = SET_ALTITUDE and parameter = 80.0 is received
  Then the drone adjusts its target altitude to 80.0 meters
  And it ascends or descends to reach the new altitude
```

```
Scenario: Broadcast command affects all drones
  Given 8 drones running in various modes
  When a DroneCommand with drone_id = 255 and command = HOVER is received
  Then all drones that are in EN_ROUTE mode transition to HOVERING
  And drones in other modes are unaffected
```

### 3.5 Landing Sequence

```
Scenario: Drone lands when reaching base station
  Given a drone in RETURNING_TO_BASE mode
  When the drone arrives within 10 meters horizontally of the base station
  Then the drone transitions to LANDING mode
  And it begins descending at 2 m/s
```

```
Scenario: Drone completes landing and returns to IDLE
  Given a drone in LANDING mode descending
  When the drone's altitude drops below 0.5 meters
  Then the drone transitions to LANDED mode
  And then automatically transitions to IDLE mode
  And ground_speed_mps is 0
  And motor RPMs drop to 0
```

---

## 4. Drone Simulation — Flight Physics

### 4.1 Kinematic Model

```
Scenario: Position updates at 10 Hz using kinematic integration
  Given a drone in EN_ROUTE mode heading north at 10 m/s
  When 100 milliseconds elapse (one update cycle)
  Then the drone's latitude increases by approximately 10 * 0.1 / 111320 degrees
  And the drone's longitude remains approximately constant
  And the published DroneState reflects the new position
```

```
Scenario: Heading adjusts toward target bearing at turn rate
  Given a drone with heading 0 degrees (north) targeting a waypoint at bearing 90 degrees (east)
  When one update cycle elapses
  Then the heading increases by at most 4.5 degrees (45 deg/s * 0.1s)
  And the heading continues adjusting each cycle until aligned with the target bearing
```

```
Scenario: Speed is bounded by maximum
  Given a drone with cruise speed set to 20 m/s (above max)
  When the drone accelerates
  Then ground_speed_mps never exceeds 15 m/s
```

```
Scenario: Acceleration is bounded
  Given a drone transitioning from hover (0 m/s) to cruise (10 m/s)
  When one update cycle elapses
  Then speed increases by at most 0.3 m/s (3 m/s^2 * 0.1s)
```

### 4.2 Altitude Control

```
Scenario: Ascent rate is 3 m/s
  Given a drone in TAKEOFF mode at altitude 0m targeting 50m
  When one second elapses
  Then altitude has increased by approximately 3 meters
```

```
Scenario: Descent rate is 2 m/s
  Given a drone in LANDING mode at altitude 20m
  When one second elapses
  Then altitude has decreased by approximately 2 meters
```

```
Scenario: Altitude is bounded by maximum
  Given a drone with target altitude set to 150m (above max 120m)
  When the drone ascends
  Then altitude never exceeds 120 meters AGL
```

---

## 5. Drone Simulation — Battery Model

### 5.1 Drain Rates

```
Scenario: Battery drains at hovering rate when stationary
  Given a drone in HOVERING mode with battery_pct = 80.0
  When 1 minute elapses
  Then battery_pct is approximately 79.5 (drain rate 0.5%/min)
```

```
Scenario: Battery drains at cruising rate during flight
  Given a drone in EN_ROUTE mode at 10 m/s with battery_pct = 80.0
  When 1 minute elapses
  Then battery_pct is approximately 79.0 (drain rate 1.0%/min)
```

```
Scenario: Battery drains faster at high speed
  Given a drone in EN_ROUTE mode at 13 m/s (above 12 m/s threshold) with battery_pct = 80.0
  When 1 minute elapses
  Then battery_pct is approximately 78.5 (drain rate 1.5%/min)
```

### 5.2 Voltage Model

```
Scenario: Battery voltage correlates with charge level
  Given a drone with battery_pct = 100.0
  Then battery_voltage is approximately 16.8V
  When battery_pct = 50.0
  Then battery_voltage is approximately 15.0V
  When battery_pct = 0.0
  Then battery_voltage is approximately 13.2V
```

### 5.3 Battery Alerts and Auto-RTB

```
Scenario: Warning alert at 30% battery
  Given a drone in EN_ROUTE mode with battery_pct above 30%
  When battery_pct drops to 30%
  Then a DroneAlert is published with alert_type = LOW_BATTERY and severity = WARNING
  And the alert message includes the current battery percentage
```

```
Scenario: Critical alert at 20% battery
  Given a drone with battery_pct above 20%
  When battery_pct drops to 20%
  Then a DroneAlert is published with alert_type = LOW_BATTERY and severity = CRITICAL
```

```
Scenario: Forced return to base at 15% battery
  Given a drone in EN_ROUTE mode with battery_pct above 15%
  When battery_pct drops to 15%
  Then the drone automatically transitions to RETURNING_TO_BASE mode
  And a DroneAlert is published with severity = CRITICAL and a message indicating forced RTB
```

---

## 6. Drone Simulation — Fault Injection

### 6.1 Motor Fault

```
Scenario: Motor anomaly reduces one motor's RPM
  Given a drone in EN_ROUTE mode with all 4 motors in normal RPM range
  When a motor anomaly fault is injected
  Then one motor's RPM drops by 30-50% from its current value
  And the other three motors remain in normal range
  And a DroneAlert is published with alert_type = MOTOR_FAULT and severity = WARNING
  And the fault clears after 30-60 seconds with RPM returning to normal
```

### 6.2 GPS Degradation

```
Scenario: GPS degradation reduces fix quality
  Given a drone with gps_satellite_count >= 8 and gps_hdop < 2.0
  When a GPS degradation fault is injected
  Then gps_satellite_count drops to 3-5
  And gps_hdop increases above 4.0
  And the drone's reported position drifts randomly by up to 2 meters
  And a DroneAlert is published with alert_type = GPS_DEGRADED and severity = WARNING
  And the fault clears after 20-40 seconds
```

### 6.3 Communication Timeout

```
Scenario: Communication timeout stops publishing temporarily
  Given a drone publishing DroneState at 10 Hz
  When a communication timeout fault is injected
  Then the drone stops publishing DroneState for 3-5 seconds
  And after the timeout, publishing resumes at 10 Hz
  And the swarm monitor detects the absence via liveliness timeout
```

### 6.4 Critical Fault

```
Scenario: Critical fault halts the drone
  Given a drone in EN_ROUTE mode
  When a critical fault is injected
  Then the drone transitions to FAULT mode
  And it stops forward motion and hovers in place
  And ground_speed_mps drops to 0
  And a DroneAlert is published with severity = CRITICAL
  And the drone remains in FAULT mode until a manual command is received
```

```
Scenario: Recovery from non-critical fault via command
  Given a drone in FAULT mode due to a non-critical fault
  When a DroneCommand with command = RETURN_TO_BASE is received
  Then the drone transitions to RETURNING_TO_BASE mode
  And it navigates toward the base station
```

---

## 7. Drone Personalities

```
Scenario: Each drone starts with its configured personality
  Given the swarm launcher starts all 8 drones
  Then each drone initializes with the following characteristics:
    | ID | Callsign | Battery | Cruise Speed | Personality Trait                  |
    | 0  | ALPHA    | 100%    | 10 m/s       | Baseline fault rates               |
    | 1  | BRAVO    | 95%     | 12 m/s       | Higher battery drain               |
    | 2  | CHARLIE  | 88%     | 10 m/s       | Lower starting battery             |
    | 3  | DELTA    | 100%    | 10 m/s       | 3x GPS degradation fault rate      |
    | 4  | ECHO     | 97%     | 10 m/s       | 3x motor fault rate                |
    | 5  | FOXTROT  | 100%    | 8 m/s        | Slower cruise speed                |
    | 6  | GOLF     | 92%     | 13 m/s       | Faster speed, higher drain rate    |
    | 7  | HOTEL    | 100%    | 10 m/s       | Starts IDLE, no auto-mission       |
```

```
Scenario: Drone 7 (HOTEL) remains idle until commanded
  Given all 8 drones are launched
  When missions are assigned to drones 0-6
  Then drone 7 remains in IDLE mode
  And drone 7 publishes DroneState with mode = IDLE and altitude = 0
  And drone 7 responds only when a DroneCommand is received
```

---

## 8. Mission Generation

### 8.1 Mission Patterns

```
Scenario: Perimeter patrol generates rectangle waypoints
  Given a mission is generated for drone 0 (ALPHA) with pattern "perimeter"
  When the mission waypoints are computed
  Then there are 8 waypoints
  And the waypoints form a rectangle along the operational area boundary
  And all waypoints are within the 2km x 2km operational area
  And cruise_altitude_m is set to a reasonable default
```

```
Scenario: Grid search generates lawn-mower pattern
  Given a mission is generated for drone 1 (BRAVO) with pattern "grid_north"
  When the mission waypoints are computed
  Then there are 12 waypoints
  And the waypoints form a back-and-forth lawn-mower pattern
  And the pattern covers the north half of the operational area
```

```
Scenario: All generated missions stay within geofence
  Given missions are generated for drones 0-6
  When I inspect every waypoint in every mission
  Then all waypoints fall within the 2km x 2km operational area centered at (37.3861, -122.0839)
```

### 8.2 Mission Publishing

```
Scenario: Missions are published via DDS on startup
  Given the swarm launcher starts
  When all drones are initialized
  Then a MissionPlan is published for each of drones 0-6
  And each MissionPlan has is_active = true
  And each MissionPlan has a non-empty mission_name
  And drone 7 receives no MissionPlan
```

---

## 9. Swarm Summary Computation

```
Scenario: Swarm summary aggregates drone states correctly
  Given 8 drones are running with the following modes:
    | Drone | Mode              |
    | 0     | EN_ROUTE          |
    | 1     | EN_ROUTE          |
    | 2     | RETURNING_TO_BASE |
    | 3     | EN_ROUTE          |
    | 4     | FAULT             |
    | 5     | EN_ROUTE          |
    | 6     | EN_ROUTE          |
    | 7     | IDLE              |
  When the swarm summary is computed
  Then active_drones = 5 (EN_ROUTE + HOVERING)
  And faulted_drones = 1
  And returning_drones = 1
  And idle_drones = 1
  And total_drones = 8
```

```
Scenario: Swarm summary tracks battery statistics
  Given drones have the following battery levels:
    | Drone | Battery |
    | 0     | 85%     |
    | 1     | 72%     |
    | 2     | 31%     |
    | 3     | 90%     |
    | 4     | 65%     |
    | 5     | 88%     |
    | 6     | 55%     |
    | 7     | 100%    |
  When the swarm summary is computed
  Then avg_battery_pct is approximately 73.25%
  And min_battery_pct = 31.0
  And min_battery_drone_id = 2
```

```
Scenario: Swarm summary is published at 1 Hz
  Given the swarm summary publisher is running
  When I subscribe to the "swarm/summary" topic
  Then I receive approximately 1 sample per second
  And each sample has summary_id = 0
  And timestamp_ns increases monotonically
```

---

## 10. WebSocket Bridge

### 10.1 Server Lifecycle

```
Scenario: Bridge starts and listens for WebSocket connections
  Given the WebSocket bridge process is launched
  When the process initializes
  Then it creates a DDS DomainParticipant on domain 0
  And it subscribes to all five topics
  And it listens for WebSocket connections on port 8765
```

```
Scenario: Dashboard connects to bridge
  Given the WebSocket bridge is running on port 8765
  When a WebSocket client connects to ws://localhost:8765
  Then the connection is accepted
  And the client begins receiving drone data messages
```

```
Scenario: Bridge handles multiple dashboard clients
  Given the WebSocket bridge is running
  When two WebSocket clients connect
  Then both clients receive the same data messages
  And a command from either client is forwarded to DDS
```

### 10.2 Data Forwarding

```
Scenario: DroneState is batched and forwarded at 5 Hz
  Given a WebSocket client is connected to the bridge
  And 8 drones are publishing DroneState at 10 Hz each
  When 1 second elapses
  Then the client receives approximately 5 "drone_state_batch" messages
  And each batch contains state for all 8 drones
  And each batch has the structure:
    {
      "type": "drone_state_batch",
      "timestamp_ns": <number>,
      "drones": [ <DroneState>, ... ]
    }
```

```
Scenario: Alerts are forwarded immediately
  Given a WebSocket client is connected
  When a DroneAlert is published on DDS
  Then the client receives a message with type = "drone_alert" within 100ms
  And the data field contains all DroneAlert fields serialized as JSON
```

```
Scenario: Mission plans are forwarded immediately
  Given a WebSocket client is connected
  When a MissionPlan is published on DDS
  Then the client receives a message with type = "mission_plan"
  And the data includes the waypoint array and mission metadata
```

```
Scenario: Swarm summary is forwarded immediately
  Given a WebSocket client is connected
  When a SwarmSummary is published on DDS
  Then the client receives a message with type = "swarm_summary"
```

### 10.3 Command Relay

```
Scenario: Dashboard command is relayed to DDS
  Given a WebSocket client is connected
  When the client sends:
    {
      "type": "drone_command",
      "data": {
        "drone_id": 3,
        "command": "RETURN_TO_BASE",
        "target_position": null,
        "parameter": 0.0
      }
    }
  Then the bridge publishes a DroneCommand on the "drone/command" topic
  And the DroneCommand has drone_id = 3 and command = RETURN_TO_BASE
  And drone 3 receives the command via its DDS subscription
```

### 10.4 Reconnection

```
Scenario: Bridge continues operating when a client disconnects
  Given two WebSocket clients are connected
  When client 1 disconnects
  Then client 2 continues receiving data normally
  And the bridge does not crash or stop
```

---

## 11. Dashboard — Connection Management

```
Scenario: Dashboard shows connection status
  Given the React dashboard is loaded in a browser
  When the WebSocket connection to the bridge is established
  Then the header displays a green "Connected" indicator
```

```
Scenario: Dashboard shows disconnected status
  Given the dashboard is connected to the bridge
  When the WebSocket connection drops
  Then the header displays a red "Disconnected" indicator
  And the dashboard attempts to reconnect automatically
```

```
Scenario: Dashboard reconnects after bridge restart
  Given the dashboard was connected and then the bridge process was stopped
  When the bridge process is restarted
  Then the dashboard automatically reconnects
  And live data resumes on the map and panels
```

---

## 12. Dashboard — Map Panel

### 12.1 Map Display

```
Scenario: Map renders centered on the operational area
  Given the dashboard is loaded and connected
  When the map panel initializes
  Then a Leaflet map is displayed with OpenStreetMap tiles
  And the map is centered on approximately (37.3861, -122.0839)
  And the zoom level shows the full 2km x 2km operational area
```

### 12.2 Drone Markers

```
Scenario: Each drone appears as a marker on the map
  Given the dashboard is receiving drone_state_batch messages
  When state for 8 drones is received
  Then 8 drone markers are visible on the map
  And each marker is positioned at the drone's reported latitude/longitude
  And each marker is rotated to reflect the drone's heading_deg
```

```
Scenario: Drone marker color reflects mode
  Given a drone with mode = EN_ROUTE
  Then its marker color is blue
  When the drone's mode changes to FAULT
  Then its marker color changes to red with a pulsing animation
  And the following color mapping applies:
    | Mode              | Color  |
    | EN_ROUTE          | Blue   |
    | HOVERING          | Cyan   |
    | RETURNING_TO_BASE | Orange |
    | FAULT             | Red    |
    | IDLE / LANDED     | Gray   |
    | TAKEOFF           | Blue   |
    | LANDING           | Orange |
```

```
Scenario: Clicking a drone marker on the map selects that drone
  Given 8 drone markers are displayed on the map
  When I click the marker for drone 3 (DELTA)
  Then drone 3 becomes the selected drone
  And the drone selector tab for drone 3 is highlighted
  And the telemetry charts and command panel update to show drone 3's data
```

### 12.3 Drone Trails

```
Scenario: Drone trails show recent flight path
  Given a drone has been flying for 30 seconds
  When trails are enabled (default)
  Then a semi-transparent polyline follows the drone's path
  And the trail represents the last 60 seconds of positions
  And older segments of the trail are more transparent than recent ones
```

```
Scenario: Trails can be toggled off
  Given drone trails are visible on the map
  When I click the "toggle trails" control
  Then all drone trails are hidden
  When I click it again
  Then trails reappear
```

### 12.4 Waypoint Paths

```
Scenario: Mission waypoint paths are displayed
  Given drone 0 has an active mission with 8 waypoints
  When waypoint display is enabled (default)
  Then dashed lines connect the waypoints in order
  And small circle markers appear at each waypoint
  And the current target waypoint is visually highlighted
```

```
Scenario: Waypoint paths can be toggled off
  Given waypoint paths are visible on the map
  When I click the "toggle waypoints" control
  Then all waypoint paths are hidden
```

### 12.5 Geofence and Base Station

```
Scenario: Geofence boundary is displayed
  Given the map is rendered
  Then a red dashed rectangle shows the 2km x 2km operational area boundary
  And the rectangle is centered on (37.3861, -122.0839)
```

```
Scenario: Base station marker is displayed
  Given the map is rendered
  Then a distinct marker (helipad or house icon) is shown at (37.3861, -122.0839)
  And the marker is visually distinct from drone markers
```

---

## 13. Dashboard — Swarm Overview Panel

```
Scenario: Status cards show drone counts by category
  Given the dashboard is receiving swarm_summary messages
  When a summary with active_drones=5, faulted_drones=1, returning_drones=1, idle_drones=1 is received
  Then the overview panel displays:
    | Card     | Value |
    | Active   | 5     |
    | Faulted  | 1     |
    | Returning| 1     |
    | Idle     | 1     |
```

```
Scenario: Battery overview shows fleet battery status
  Given a swarm_summary with avg_battery_pct=73.25, min_battery_pct=31.0, min_battery_drone_id=2
  When the overview panel updates
  Then it displays "Avg Battery: 73%" with a progress bar
  And it displays "Min Battery: 31% (CHARLIE)" identifying the lowest drone by callsign
```

```
Scenario: Mission stats are displayed
  Given a swarm_summary with missions_completed=3 and active_alerts=2
  When the overview panel updates
  Then it displays "Missions Done: 3"
  And it displays "Active Alerts: 2"
```

---

## 14. Dashboard — Alert Feed

```
Scenario: Alerts appear in real time
  Given the alert feed panel is visible
  When a DroneAlert with alert_type=LOW_BATTERY, severity=WARNING, drone_id=2 arrives
  Then a new entry appears at the top of the alert feed
  And the entry shows drone callsign "CHARLIE"
  And the entry shows the alert message text
  And the entry has a warning-level severity icon
```

```
Scenario: Alert severity is visually distinguished
  Given multiple alerts with different severities
  Then CRITICAL alerts have a red/danger icon
  And WARNING alerts have an orange/yellow warning icon
  And INFO alerts have a blue/neutral icon
```

```
Scenario: Alert feed is bounded and scrollable
  Given more than 20 alerts have been received
  Then the alert feed shows the most recent alerts at the top
  And the feed is scrollable to see older alerts
  And at most 100 alerts are retained in the feed
```

```
Scenario: Critical alerts have visual emphasis
  Given a DroneAlert with severity = CRITICAL arrives
  Then the alert entry has a pulsing or highlighted visual treatment
  And it is visually distinct from WARNING and INFO entries
```

---

## 15. Dashboard — Drone Selector

```
Scenario: Drone selector shows all 8 drones
  Given the dashboard is loaded and receiving data
  Then 8 clickable drone tabs are displayed
  And each tab shows the drone ID and callsign
  And the currently selected drone's tab is highlighted
```

```
Scenario: Drone tabs are color-coded by status
  Given drone 4 is in FAULT mode
  Then drone 4's tab has a red indicator
  And drones in EN_ROUTE mode have a blue indicator
  And drones in IDLE mode have a gray indicator
```

```
Scenario: Clicking a drone tab changes the selected drone
  Given drone 0 (ALPHA) is currently selected
  When I click the tab for drone 5 (FOXTROT)
  Then drone 5 becomes the selected drone
  And the telemetry charts switch to drone 5's historical data
  And the command panel targets drone 5
```

---

## 16. Dashboard — Telemetry Charts

### 16.1 Chart Data

```
Scenario: Battery chart shows rolling history
  Given drone 0 is selected and has been publishing for 60 seconds
  When the battery chart renders
  Then it displays a line chart of battery_pct over time
  And the time window shows the last 2 minutes of data
  And the Y-axis is labeled in percent (%)
  And the line trends downward as battery drains
```

```
Scenario: Altitude chart shows flight profile
  Given drone 0 is selected
  When the altitude chart renders
  Then it displays a line chart of altitude_m over time
  And the Y-axis is labeled in meters (m)
  And the chart reflects takeoff, cruise, and any altitude changes
```

```
Scenario: Speed chart shows velocity over time
  Given drone 0 is selected
  When the speed chart renders
  Then it displays a line chart of ground_speed_mps over time
  And the Y-axis is labeled in m/s
```

```
Scenario: Motor RPM chart shows all four motors
  Given drone 0 is selected
  When the motor RPM chart renders
  Then it displays 4 overlaid lines, one per motor
  And each line is a different color
  And the time window is 30 seconds
  And during a motor fault, one line visibly drops
```

```
Scenario: Temperature chart shows internal temp
  Given drone 0 is selected
  When the temperature chart renders
  Then it displays a line chart of internal_temp_c over time
  And the Y-axis is labeled in degrees Celsius
  And the time window is 5 minutes
```

### 16.2 Chart Behavior

```
Scenario: Charts update in real time without animation lag
  Given any telemetry chart is visible
  When new drone state data arrives
  Then the chart appends the new data point
  And old data points beyond the time window are removed
  And the update is smooth without animation jitter
```

```
Scenario: Charts switch data when selected drone changes
  Given drone 0 is selected and battery chart shows drone 0 data
  When I select drone 3
  Then the battery chart clears and shows drone 3's battery history
  And all other charts also switch to drone 3's data
```

---

## 17. Dashboard — Command Panel

### 17.1 Quick Commands

```
Scenario: Return to Base button sends RTB command
  Given drone 3 is selected
  When I click the "Return to Base" button
  Then a WebSocket message is sent:
    { "type": "drone_command", "data": { "drone_id": 3, "command": "RETURN_TO_BASE" } }
  And drone 3 transitions to RETURNING_TO_BASE mode on the map
```

```
Scenario: Hover button sends hover command
  Given drone 1 is selected and in EN_ROUTE mode
  When I click the "Hover" button
  Then a hover command is sent for drone 1
  And drone 1 transitions to HOVERING on the map
```

```
Scenario: Resume Mission button sends resume command
  Given drone 1 is selected and in HOVERING mode
  When I click the "Resume Mission" button
  Then a resume mission command is sent for drone 1
```

```
Scenario: Emergency Land button sends emergency land command
  Given drone 4 is selected and in FAULT mode
  When I click the "Emergency Land" button
  Then an emergency land command is sent for drone 4
```

### 17.2 Parameter Commands

```
Scenario: Set Speed sends speed command with parameter
  Given drone 0 is selected
  When I enter 13 in the speed input and click "Set Speed"
  Then a SET_SPEED command with parameter = 13.0 is sent for drone 0
```

```
Scenario: Set Altitude sends altitude command with parameter
  Given drone 0 is selected
  When I enter 80 in the altitude input and click "Set Altitude"
  Then a SET_ALTITUDE command with parameter = 80.0 is sent for drone 0
```

### 17.3 Go To Waypoint

```
Scenario: Go To Waypoint sends drone to specified coordinates
  Given drone 0 is selected
  When I enter latitude = 37.388, longitude = -122.085, altitude = 60 and click "Go To Waypoint"
  Then a GOTO_WAYPOINT command is sent with the specified target_position
```

### 17.4 Broadcast

```
Scenario: Broadcast toggle sends command to all drones
  Given the "Send to All Drones" toggle is enabled
  When I click "Hover"
  Then a hover command is sent with drone_id = 255
  And all active drones transition to HOVERING
```

---

## 18. Dashboard — Dark Mode

```
Scenario: Dashboard defaults to dark mode
  Given the dashboard loads for the first time
  Then the UI renders in dark mode
  And the background color is #1A1A2E
  And the card background is #16213E
  And text is light-colored (#E0E0E0)
```

```
Scenario: Dark mode toggle switches to light mode
  Given the dashboard is in dark mode
  When I click the dark mode toggle in the header
  Then the UI switches to light mode
  And background changes to #FFFFFF
  And card background changes to #F5F5F5
  And text changes to dark (#333333)
  And all charts and map adjust their color scheme
```

```
Scenario: Theme preference persists across page reloads
  Given I switch to light mode
  When I reload the browser page
  Then the dashboard loads in light mode
```

---

## 19. Dashboard — Telemetry Data Management

```
Scenario: Historical data is stored as ring buffers
  Given a drone has been publishing state for 3 minutes
  Then the dashboard retains the last 120 seconds of telemetry history
  And data older than 120 seconds is discarded
  And memory usage remains stable over time
```

```
Scenario: Trail data covers 60 seconds
  Given a drone has been flying for 2 minutes
  Then the trail polyline on the map contains the last 60 seconds of positions
  And positions older than 60 seconds are removed from the trail
```

---

## 20. End-to-End Integration

### 20.1 Full System Startup

```
Scenario: Entire system starts and data flows end-to-end
  Given all Python processes are started (drones, bridge)
  And the React dashboard is running
  When I open the dashboard in a browser
  Then I see 8 drone markers on the map
  And drones 0-6 are moving along their mission paths
  And drone 7 is stationary at the base station
  And the swarm overview shows correct counts
  And the alert feed begins populating as faults occur
  And telemetry charts show live data for the selected drone
```

### 20.2 Interactive Command Flow

```
Scenario: Operator sends command and sees result on dashboard
  Given the full system is running and the dashboard is open
  When I select drone 1 (BRAVO) and click "Return to Base"
  Then drone 1's marker on the map changes color to orange
  And drone 1's marker begins moving toward the base station
  And the swarm overview updates returning_drones count
  And drone 1's speed chart reflects deceleration and course change
```

### 20.3 Fault Observation

```
Scenario: Fault appears on dashboard without operator action
  Given the full system is running for several minutes
  When a motor fault is injected on drone 4 (ECHO)
  Then a WARNING alert appears in the alert feed mentioning ECHO
  And drone 4's motor RPM chart shows one line dropping
  And if I select drone 4, the telemetry panel shows the degraded motor
```

### 20.4 Low Battery Sequence

```
Scenario: Drone with low starting battery triggers full battery event sequence
  Given the system has been running long enough for drone 2 (CHARLIE) to reach 30% battery
  Then a LOW_BATTERY WARNING alert appears in the feed
  When CHARLIE reaches 20% battery
  Then a LOW_BATTERY CRITICAL alert appears
  When CHARLIE reaches 15% battery
  Then CHARLIE's marker turns orange and begins returning to base
  And the swarm overview updates to reflect one more returning drone
```

---

## 21. Performance and Stability

```
Scenario: Dashboard maintains responsiveness under full data load
  Given 8 drones publishing at 10 Hz (80 state messages/sec on DDS)
  And the bridge batches to 5 Hz (5 batched messages/sec on WebSocket)
  When the dashboard has been running for 10 minutes
  Then the UI remains responsive (no visible lag or frame drops)
  And browser memory usage is stable (no unbounded growth)
  And map marker positions update smoothly
```

```
Scenario: Bridge handles WebSocket client disconnect gracefully
  Given the bridge is forwarding data to a connected dashboard
  When the browser tab is closed
  Then the bridge logs the disconnection
  And continues operating for other clients or future connections
  And no unhandled exceptions occur
```

```
Scenario: Drone simulators run independently
  Given all 8 drone simulators are running
  When drone 4's process is killed
  Then drones 0-3 and 5-7 continue operating normally
  And the swarm summary reflects 7 total reporting drones
  And the dashboard shows drone 4's marker becoming stale or disappearing
```
