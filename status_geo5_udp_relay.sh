#!/bin/bash
# Verifica el estado del relay UDP GEO5 (geo5_udp_relay.py)
# Uso: ./status_geo5_udp_relay.sh

SCRIPT_NAME="geo5_udp_relay.py"
PID_FILE="/tmp/geo5_udp_relay.pid"
PROCESS_LOG="geo5_udp_relay.log"
LOG_DIR="logsUDP"
UDP_PORT="6003"
CONFIG_FILE="REENVIOS_CONFIG_UDP.txt"

LATEST_LOG=$(ls -t ${LOG_DIR}/LOG_*.txt 2>/dev/null | head -1)
LATEST_REENVIOS=$(ls -t ${LOG_DIR}/Reenvios_*.log 2>/dev/null | head -1)
LATEST_RELAY=$(ls -t ${LOG_DIR}/Relay_*.log 2>/dev/null | head -1)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  ESTADO DEL RELAY UDP GEO5${NC}"
echo -e "${BLUE}=====================================${NC}"

get_process_info() {
    local pid=$1
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        local cmd=$(ps -p "$pid" -o cmd= 2>/dev/null | tr -d '\n')
        local start_time=$(ps -p "$pid" -o lstart= 2>/dev/null | tr -d '\n')
        local cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | tr -d ' ')
        local mem=$(ps -p "$pid" -o %mem= 2>/dev/null | tr -d ' ')

        echo -e "   ${GREEN}[OK] Estado:${NC} Ejecutandose"
        echo -e "   ${BLUE}PID:${NC} $pid"
        echo -e "   ${BLUE}Iniciado:${NC} $start_time"
        echo -e "   ${BLUE}CPU:${NC} ${cpu}%"
        echo -e "   ${BLUE}Memoria:${NC} ${mem}%"
        echo -e "   ${BLUE}Comando:${NC} $cmd"
        return 0
    else
        echo -e "   ${RED}[ERROR] Estado:${NC} No ejecutandose"
        return 1
    fi
}

echo -e "\n${CYAN}--- PROCESO DEL RELAY ---${NC}"
RELAY_RUNNING=false
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo -e "${BLUE}Archivo PID:${NC} $PID_FILE"
    echo -e "${BLUE}PID registrado:${NC} $PID"

    if get_process_info "$PID"; then
        RELAY_RUNNING=true
    else
        echo -e "${YELLOW}[WARN] El PID registrado no esta ejecutandose${NC}"
    fi
else
    echo -e "${YELLOW}[WARN] No se encuentra archivo PID: $PID_FILE${NC}"
fi

echo -e "\n${CYAN}--- BUSQUEDA DE PROCESOS ---${NC}"
ALL_PIDS=$(pgrep -f "$SCRIPT_NAME")

if [ -n "$ALL_PIDS" ]; then
    echo -e "${GREEN}[OK] Procesos encontrados: $ALL_PIDS${NC}"

    if [ "$RELAY_RUNNING" = false ]; then
        echo -e "${YELLOW}[WARN] Hay procesos ejecutandose pero no estan registrados en PID file${NC}"
        echo -e "${BLUE}Informacion de procesos encontrados:${NC}"
        for pid in $ALL_PIDS; do
            echo -e "\n${CYAN}--- Proceso PID: $pid ---${NC}"
            get_process_info "$pid"
        done
        RELAY_RUNNING=true
    fi
else
    echo -e "${RED}[ERROR] No se encontraron procesos del relay${NC}"
fi

echo -e "\n${CYAN}--- CONFIGURACION ---${NC}"
if [ -f "$CONFIG_FILE" ]; then
    CONFIG_LINES=$(grep -v '^#' "$CONFIG_FILE" | grep -v '^[[:space:]]*$' | grep -v '^TIPO,' | wc -l)
    CONFIG_MTIME=$(stat -c '%y' "$CONFIG_FILE" 2>/dev/null || stat -f '%Sm' "$CONFIG_FILE" 2>/dev/null)
    echo -e "${GREEN}[OK] Archivo config:${NC} $CONFIG_FILE"
    echo -e "   ${BLUE}Reglas activas (aprox.):${NC} $CONFIG_LINES"
    echo -e "   ${BLUE}Ultima modificacion:${NC} $CONFIG_MTIME"
else
    echo -e "${YELLOW}[WARN] No se encuentra $CONFIG_FILE${NC}"
fi

echo -e "\n${CYAN}--- ARCHIVOS DE LOG ---${NC}"
if [ -d "$LOG_DIR" ]; then
    echo -e "${GREEN}[OK] Directorio de logs:${NC} $LOG_DIR"

    LOG_COUNT=$(ls -1 ${LOG_DIR}/LOG_*.txt 2>/dev/null | wc -l)
    if [ "$LOG_COUNT" -gt 0 ]; then
        echo -e "${BLUE}Archivos LOG_*.txt:${NC} $LOG_COUNT"
        echo -e "\n${BLUE}Ultimos archivos de trafico:${NC}"
        ls -lth ${LOG_DIR}/LOG_*.txt 2>/dev/null | head -3 | awk '{print "   " $9 " (" $5 ")"}'
    else
        echo -e "${YELLOW}[WARN] No se encontraron LOG_*.txt${NC}"
    fi
else
    echo -e "${YELLOW}[WARN] Directorio de logs no existe: $LOG_DIR${NC}"
fi

if [ -f "$PROCESS_LOG" ]; then
    PROC_SIZE=$(du -h "$PROCESS_LOG" | cut -f1)
    echo -e "\n${GREEN}[OK] Log del proceso:${NC} $PROCESS_LOG ($PROC_SIZE)"
else
    echo -e "\n${YELLOW}[WARN] Log del proceso no encontrado: $PROCESS_LOG${NC}"
fi

if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
    LOG_SIZE=$(du -h "$LATEST_LOG" | cut -f1)
    LOG_LINES=$(wc -l < "$LATEST_LOG" 2>/dev/null || echo "0")
    LOG_NAME=$(basename "$LATEST_LOG")

    echo -e "\n${GREEN}[OK] Log de trafico actual:${NC} $LOG_NAME"
    echo -e "   ${BLUE}Tamaño:${NC} $LOG_SIZE"
    echo -e "   ${BLUE}Lineas:${NC} $LOG_LINES"

    echo -e "\n${BLUE}Ultimas 10 lineas de trafico:${NC}"
    echo -e "${CYAN}---${NC}"
    tail -10 "$LATEST_LOG" | sed 's/^/   /'
    echo -e "${CYAN}---${NC}"
fi

if [ -n "$LATEST_REENVIOS" ] && [ -f "$LATEST_REENVIOS" ]; then
    REENV_NAME=$(basename "$LATEST_REENVIOS")
    REENV_LINES=$(wc -l < "$LATEST_REENVIOS" 2>/dev/null || echo "0")
    echo -e "\n${GREEN}[OK] Log de reenvios:${NC} $REENV_NAME ($REENV_LINES lineas)"
fi

if [ -n "$LATEST_RELAY" ] && [ -f "$LATEST_RELAY" ]; then
    RELAY_NAME=$(basename "$LATEST_RELAY")
    echo -e "\n${BLUE}Ultimas 5 lineas del log de aplicacion ($RELAY_NAME):${NC}"
    echo -e "${CYAN}---${NC}"
    tail -5 "$LATEST_RELAY" | sed 's/^/   /'
    echo -e "${CYAN}---${NC}"
fi

echo -e "\n${CYAN}--- PUERTOS DE RED ---${NC}"
UDP_LISTENING=false
if command -v ss >/dev/null 2>&1; then
    if ss -ulnp 2>/dev/null | grep -q ":${UDP_PORT} "; then
        UDP_LISTENING=true
    fi
elif netstat -uln 2>/dev/null | grep -q ":${UDP_PORT} "; then
    UDP_LISTENING=true
fi

if [ "$UDP_LISTENING" = true ]; then
    echo -e "${GREEN}[OK] Puerto UDP ${UDP_PORT}:${NC} Escuchando"
else
    echo -e "${RED}[ERROR] Puerto UDP ${UDP_PORT}:${NC} No escuchando"
fi

echo -e "\n${CYAN}--- ESTADISTICAS DEL SISTEMA ---${NC}"
echo -e "${BLUE}Fecha/Hora:${NC} $(date)"
if command -v uptime >/dev/null 2>&1; then
    echo -e "${BLUE}Uptime:${NC} $(uptime | awk -F'up ' '{print $2}' | awk -F', load' '{print $1}')"
fi

echo -e "\n${CYAN}--- RESUMEN ---${NC}"
if [ "$RELAY_RUNNING" = true ]; then
    echo -e "${GREEN}[OK] Relay: Ejecutandose${NC}"
    echo -e "${BLUE}Para detener:${NC} ./stop_geo5_udp_relay.sh"
else
    echo -e "${RED}[ERROR] Relay: No ejecutandose${NC}"
    echo -e "${BLUE}Para iniciar:${NC} ./start_geo5_udp_relay.sh"
fi

if [ "$UDP_LISTENING" = true ]; then
    echo -e "${GREEN}[OK] UDP ${UDP_PORT}: Activo${NC}"
else
    echo -e "${RED}[ERROR] UDP ${UDP_PORT}: Inactivo${NC}"
fi

echo -e "\n${CYAN}--- COMANDOS DISPONIBLES ---${NC}"
echo -e "${YELLOW}Iniciar:${NC} ./start_geo5_udp_relay.sh"
echo -e "${YELLOW}Detener:${NC} ./stop_geo5_udp_relay.sh"
echo -e "${YELLOW}Estado:${NC} ./status_geo5_udp_relay.sh"
if [ -n "$LATEST_LOG" ]; then
    echo -e "${YELLOW}Trafico:${NC} tail -f $LATEST_LOG"
fi
if [ -f "$PROCESS_LOG" ]; then
    echo -e "${YELLOW}Proceso:${NC} tail -f $PROCESS_LOG"
fi

echo -e "\n${BLUE}=====================================${NC}"
