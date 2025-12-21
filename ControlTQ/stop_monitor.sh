#!/bin/bash
# stop_monitor.sh
# Script para detener el monitor de heartbeat

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/monitor.pid"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$SCRIPT_DIR"

if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No se encuentra PID file. El monitor puede no estar corriendo.${NC}"
    exit 1
fi

MONITOR_PID=$(cat "$PID_FILE")

if ! ps -p "$MONITOR_PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}El proceso $MONITOR_PID no está corriendo${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "Deteniendo monitor (PID: $MONITOR_PID)..."
kill "$MONITOR_PID"

# Esperar hasta 5 segundos para que termine
for i in {1..5}; do
    if ! ps -p "$MONITOR_PID" > /dev/null 2>&1; then
        echo -e "${GREEN}Monitor detenido correctamente${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Si todavía está corriendo, forzar
if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}Forzando detención...${NC}"
    kill -9 "$MONITOR_PID"
    sleep 1
    if ! ps -p "$MONITOR_PID" > /dev/null 2>&1; then
        echo -e "${GREEN}Monitor detenido (forzado)${NC}"
        rm -f "$PID_FILE"
        exit 0
    else
        echo -e "${RED}Error: No se pudo detener el monitor${NC}"
        exit 1
    fi
fi
