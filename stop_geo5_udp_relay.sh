#!/bin/bash
# Detiene el relay UDP GEO5 (geo5_udp_relay.py).
# Uso: ./stop_geo5_udp_relay.sh

SCRIPT_NAME="geo5_udp_relay.py"
PID_FILE="/tmp/geo5_udp_relay.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}DETENIENDO RELAY UDP GEO5${NC}"
echo "=================================="

_stop_pids() {
    for pid in "$@"; do
        kill -TERM "$pid" 2>/dev/null
        sleep 1
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -KILL "$pid" 2>/dev/null
        fi
    done
}

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${BLUE}Deteniendo PID $PID...${NC}"
        _stop_pids "$PID"
    fi
    rm -f "$PID_FILE"
fi

PIDS=$(pgrep -f "$SCRIPT_NAME")
if [ -n "$PIDS" ]; then
    echo -e "${YELLOW}Deteniendo procesos restantes: $PIDS${NC}"
    _stop_pids $PIDS
fi

REMAINING=$(pgrep -f "$SCRIPT_NAME")
if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}Relay detenido${NC}"
else
    echo -e "${RED}Quedan procesos: $REMAINING${NC}"
    exit 1
fi
