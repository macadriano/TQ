#!/bin/bash
# stop_monitor.sh - Stops the monitor_server.py background process

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PID_FILE="$SCRIPT_DIR/monitor.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "PID file not found. Is the monitor running?"
    exit 1
fi

PID=$(cat "$PID_FILE")
if kill -0 $PID 2>/dev/null; then
    kill $PID
    echo "Monitor process $PID stopped."
    rm -f "$PID_FILE"
else
    echo "No process with PID $PID found. Cleaning up PID file."
    rm -f "$PID_FILE"
fi
