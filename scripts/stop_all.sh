#!/bin/bash
# Stop all drone swarm processes
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/.pids" ]; then
    while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping PID $pid..."
            kill "$pid" 2>/dev/null
        fi
    done < "$PROJECT_DIR/.pids"
    rm -f "$PROJECT_DIR/.pids"
    echo "All processes stopped."
else
    echo "No PID file found. Trying to find processes..."
    pkill -f "drones.run_swarm" 2>/dev/null && echo "Stopped swarm."
    pkill -f "vite" 2>/dev/null && echo "Stopped dashboard."
fi
