#!/bin/bash
# Inicia el relay UDP GEO5 (geo5_udp_relay.py) en segundo plano.
# Uso: ./start_geo5_udp_relay.sh

SCRIPT_NAME="geo5_udp_relay.py"
PID_FILE="/tmp/geo5_udp_relay.pid"
LOG_FILE="geo5_udp_relay.log"
PYTHON_CMD="python3"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}INICIANDO RELAY UDP GEO5${NC}"
echo "=================================="

if [ ! -f "$SCRIPT_NAME" ]; then
    echo -e "${RED}Error: no se encuentra $SCRIPT_NAME${NC}"
    exit 1
fi

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}El relay ya está ejecutándose (PID: $PID)${NC}"
        echo "   Para detenerlo: ./stop_geo5_udp_relay.sh"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo -e "${RED}Error: Python3 no está instalado${NC}"
    exit 1
fi

if [ ! -f "protocolo.py" ] || [ ! -f "reenvios_config.py" ]; then
    echo -e "${RED}Error: faltan protocolo.py o reenvios_config.py${NC}"
    exit 1
fi

mkdir -p logsUDP

echo -e "${BLUE}Iniciando relay en segundo plano...${NC}"
nohup "$PYTHON_CMD" "$SCRIPT_NAME" --daemon --port 6003 > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

sleep 2

if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}Relay iniciado correctamente${NC}"
    echo -e "   PID: $SERVER_PID"
    echo -e "   Log proceso: $LOG_FILE"
    echo -e "   Logs tráfico: logsUDP/"
    echo -e "   Puerto UDP: 6003"
    echo -e "   Config: REENVIOS_CONFIG_UDP.txt"
else
    echo -e "${RED}Error: el relay no pudo iniciarse${NC}"
    echo -e "   Revisar: cat $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
