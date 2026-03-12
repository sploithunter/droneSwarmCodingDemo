#!/bin/bash
# Start the drone swarm simulation and dashboard
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== DDS Drone Swarm Monitor ==="
echo ""

# Start the swarm simulation (includes bridge)
echo "Starting swarm simulation + WebSocket bridge..."
cd "$PROJECT_DIR"
python -m drones.run_swarm &
SWARM_PID=$!
echo "  Swarm PID: $SWARM_PID"

# Wait for WebSocket server to be ready
sleep 2

# Start the React dashboard dev server
echo "Starting React dashboard..."
cd "$PROJECT_DIR/dashboard"
npm run dev &
DASHBOARD_PID=$!
echo "  Dashboard PID: $DASHBOARD_PID"

echo ""
echo "=== System Running ==="
echo "  Dashboard: http://localhost:5173"
echo "  WebSocket: ws://localhost:8765"
echo ""
echo "Press Ctrl+C to stop all processes."

# Save PIDs for stop script
echo "$SWARM_PID" > "$PROJECT_DIR/.pids"
echo "$DASHBOARD_PID" >> "$PROJECT_DIR/.pids"

# Wait for interrupt
trap "kill $SWARM_PID $DASHBOARD_PID 2>/dev/null; rm -f '$PROJECT_DIR/.pids'; echo 'Stopped.'" EXIT
wait
