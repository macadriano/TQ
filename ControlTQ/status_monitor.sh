#!/bin/bash
# status_monitor.sh
# Script para ver el estado del monitor de heartbeat

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/monitor.pid"
LOG_FILE="$SCRIPT_DIR/monitor.log"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd "$SCRIPT_DIR"

echo -e "${BLUE}=== Estado del Monitor de Heartbeat ===${NC}"
echo ""

if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}Estado: NO está corriendo${NC}"
    echo "No se encuentra PID file."
    exit 1
fi

MONITOR_PID=$(cat "$PID_FILE")

if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}Estado: CORRIENDO${NC}"
    echo -e "PID: $MONITOR_PID"
    
    # Información del proceso
    PROCESS_INFO=$(ps -p "$MONITOR_PID" -o pid,etime,cmd --no-headers)
    echo -e "Información: $PROCESS_INFO"
    echo ""
    
    # Últimas líneas del log
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}Últimas 15 líneas del log:${NC}"
        echo "----------------------------------------"
        tail -n 15 "$LOG_FILE"
    else
        echo -e "${YELLOW}No se encuentra el archivo de log${NC}"
    fi
else
    echo -e "${RED}Estado: NO está corriendo (PID file existe pero proceso no encontrado)${NC}"
    echo "Limpiando PID file..."
    rm -f "$PID_FILE"
    exit 1
fi
