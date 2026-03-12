"""DDS-to-WebSocket bridge for drone swarm dashboard."""
import asyncio
import json
import time
from dataclasses import asdict
from drones.types import (
    DroneState, DroneCommand, DroneAlert, MissionPlan, SwarmSummary,
    GeoPoint, CommandType, DroneMode, AlertType, AlertSeverity
)


class _DDSEncoder(json.JSONEncoder):
    """JSON encoder that handles DDS sequence types (Float64Seq, etc.)."""
    def default(self, o):
        # DDS sequences are iterable but not JSON-serializable
        if hasattr(o, '__iter__') and not isinstance(o, (str, bytes, dict)):
            return list(o)
        return super().default(o)


def _to_json_dict(d):
    """Recursively convert DDS sequence types to plain lists for JSON."""
    if isinstance(d, dict):
        return {k: _to_json_dict(v) for k, v in d.items()}
    if isinstance(d, (list, tuple)):
        return [_to_json_dict(i) for i in d]
    if hasattr(d, '__iter__') and not isinstance(d, (str, bytes)):
        return [_to_json_dict(i) for i in d]
    return d


def serialize_state(state):
    """Serialize a DroneState to a JSON-compatible dict."""
    if isinstance(state, dict):
        return _to_json_dict(state)
    return _to_json_dict(asdict(state))


def serialize_alert(alert):
    """Serialize a DroneAlert to a JSON-compatible dict."""
    if isinstance(alert, dict):
        return _to_json_dict(alert)
    return _to_json_dict(asdict(alert))


def serialize_mission(mission):
    """Serialize a MissionPlan to a JSON-compatible dict."""
    if isinstance(mission, dict):
        return _to_json_dict(mission)
    return _to_json_dict(asdict(mission))


def serialize_summary(summary):
    """Serialize a SwarmSummary to a JSON-compatible dict."""
    if isinstance(summary, dict):
        return _to_json_dict(summary)
    return _to_json_dict(asdict(summary))


def deserialize_command(data):
    """Deserialize a JSON dict into a DroneCommand."""
    cmd_data = data.get("data", data)

    # Map command string to CommandType
    command = cmd_data.get("command", 0)
    if isinstance(command, str):
        command = CommandType[command].value

    target = cmd_data.get("target_position") or {}
    target_pos = GeoPoint(
        latitude=target.get("latitude", 0.0) if target else 0.0,
        longitude=target.get("longitude", 0.0) if target else 0.0,
        altitude_m=target.get("altitude_m", 0.0) if target else 0.0,
    )

    return DroneCommand(
        drone_id=cmd_data.get("drone_id", 0),
        timestamp_ns=int(time.time() * 1e9),
        command=command,
        target_position=target_pos,
        parameter=float(cmd_data.get("parameter", 0.0)),
        command_seq=cmd_data.get("command_seq", 0),
        issuer=cmd_data.get("issuer", "dashboard"),
    )


class WebSocketBridge:
    """WebSocket server that bridges DDS data to browser clients."""

    def __init__(self, host="0.0.0.0", port=8765, command_callback=None):
        self.host = host
        self.port = port
        self.clients = set()
        self.command_callback = command_callback or (lambda cmd: None)

        # State batching
        self._state_buffer = {}  # drone_id -> latest state dict
        self._batch_interval = 0.2  # 5Hz
        self._last_batch_time = 0

    def on_drone_state(self, state):
        """Called when a DroneState is received (from DDS or simulation)."""
        state_dict = serialize_state(state)
        drone_id = state_dict.get("drone_id", state.drone_id if hasattr(state, 'drone_id') else 0)
        self._state_buffer[drone_id] = state_dict

    def on_alert(self, alert):
        """Called when a DroneAlert is received."""
        msg = json.dumps({
            "type": "drone_alert",
            "data": serialize_alert(alert)
        })
        asyncio.ensure_future(self._broadcast(msg))

    def on_mission(self, mission):
        """Called when a MissionPlan is received."""
        msg = json.dumps({
            "type": "mission_plan",
            "data": serialize_mission(mission)
        })
        asyncio.ensure_future(self._broadcast(msg))

    def on_summary(self, summary):
        """Called when a SwarmSummary is received."""
        msg = json.dumps({
            "type": "swarm_summary",
            "data": serialize_summary(summary)
        })
        asyncio.ensure_future(self._broadcast(msg))

    def flush_batch(self):
        """Create a batched state message from buffer. Returns JSON string or None."""
        if not self._state_buffer:
            return None

        now = time.time()
        if now - self._last_batch_time < self._batch_interval:
            return None

        self._last_batch_time = now

        batch_msg = {
            "type": "drone_state_batch",
            "timestamp_ns": int(now * 1e9),
            "drones": list(self._state_buffer.values())
        }
        self._state_buffer.clear()
        return json.dumps(batch_msg)

    async def _broadcast(self, message):
        """Send message to all connected clients."""
        if not self.clients:
            return
        disconnected = set()
        for client in self.clients.copy():
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        self.clients -= disconnected

    async def _handle_client(self, websocket):
        """Handle a single WebSocket client connection."""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "drone_command":
                        cmd = deserialize_command(data)
                        self.command_callback(cmd)
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
        except Exception:
            pass
        finally:
            self.clients.discard(websocket)

    async def _batch_loop(self):
        """Periodically flush batched state updates."""
        while True:
            batch_json = self.flush_batch()
            if batch_json:
                await self._broadcast(batch_json)
            await asyncio.sleep(self._batch_interval)

    async def start(self):
        """Start the WebSocket server."""
        import websockets

        self._server = await websockets.serve(
            self._handle_client, self.host, self.port
        )
        asyncio.ensure_future(self._batch_loop())
        return self._server


def create_batch_message(states):
    """Utility: create a drone_state_batch JSON message from a list of states."""
    drones = [serialize_state(s) for s in states]
    return {
        "type": "drone_state_batch",
        "timestamp_ns": int(time.time() * 1e9),
        "drones": drones,
    }
