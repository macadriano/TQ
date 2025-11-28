#!/bin/bash
# start_monitor.sh - Starts the monitor_server.py script in background

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PYTHON_EXEC=$(which python3 || which python)
MONITOR_SCRIPT="$SCRIPT_DIR/monitor_server.py"
LOG_FILE="$SCRIPT_DIR/monitor.log"

if [[ ! -f "$MONITOR_SCRIPT" ]]; then
    echo "Monitor script not found at $MONITOR_SCRIPT"
    exit 1
fi

# Start the monitor in background, redirect output to log
nohup "$PYTHON_EXEC" "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
PID=$!

echo "Monitor started with PID $PID"
# Save PID to file for later stop
echo $PID > "$SCRIPT_DIR/monitor.pid"
