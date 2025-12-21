#!/bin/bash
# start_monitor.sh
# Script para iniciar el monitor de heartbeat en modo daemon

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/heartbeat_monitor.py"
PID_FILE="$SCRIPT_DIR/monitor.pid"
LOG_FILE="$SCRIPT_DIR/monitor.log"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$SCRIPT_DIR"

# Verificar si ya está corriendo
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}El monitor ya está corriendo (PID: $OLD_PID)${NC}"
        exit 1
    else
        echo -e "${YELLOW}Eliminando PID file obsoleto...${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Verificar que existe el script
if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo -e "${RED}Error: No se encuentra $MONITOR_SCRIPT${NC}"
    exit 1
fi

# Verificar que existe config.py
if [ ! -f "$SCRIPT_DIR/config.py" ]; then
    echo -e "${RED}Error: No se encuentra config.py${NC}"
    exit 1
fi

# Iniciar en background
echo -e "${GREEN}Iniciando monitor de heartbeat...${NC}"
nohup python3 "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
MONITOR_PID=$!

# Guardar PID
echo $MONITOR_PID > "$PID_FILE"

# Esperar un momento y verificar que está corriendo
sleep 1
if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}Monitor iniciado correctamente (PID: $MONITOR_PID)${NC}"
    echo -e "Log: $LOG_FILE"
    echo -e "Para detener: ./stop_monitor.sh"
else
    echo -e "${RED}Error: El monitor no pudo iniciarse${NC}"
    rm -f "$PID_FILE"
    exit 1
fi
