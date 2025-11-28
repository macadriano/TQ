#!/bin/bash
# status_monitor.sh - Shows the status of the monitoring process

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PID_FILE="$SCRIPT_DIR/monitor.pid"
LOG_FILE="$SCRIPT_DIR/monitor.log"

if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        echo "Monitor is running (PID $PID)"
    else
        echo "Monitor PID file exists but process is not running."
    fi
else
    echo "Monitor is not running (no PID file)."
fi

# Optionally show last few lines of log
if [[ -f "$LOG_FILE" ]]; then
    echo "--- Last 10 lines of monitor log ---"
    tail -n 10 "$LOG_FILE"
fi
