#!/bin/bash
# Script para verificar el estado del servidor TQ+RPG
# Uso: ./server_status_rpg.sh

# Configuración
SCRIPT_NAME="tq_server_rpg.py"
PID_FILE="/tmp/tq_server_rpg.pid"
LOG_DIR="logs"

# Obtener el archivo de log más reciente
LATEST_LOG=$(ls -t ${LOG_DIR}/LOG_*.txt 2>/dev/null | head -1)

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  ESTADO DEL SERVIDOR TQ+RPG${NC}"
echo -e "${BLUE}=====================================${NC}"

# Función para obtener información del proceso
get_process_info() {
    local pid=$1
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        # Información básica del proceso
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

# Verificar archivo PID
echo -e "\n${CYAN}--- PROCESO DEL SERVIDOR ---${NC}"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo -e "${BLUE}Archivo PID:${NC} $PID_FILE"
    echo -e "${BLUE}PID registrado:${NC} $PID"
    
    if get_process_info "$PID"; then
        SERVER_RUNNING=true
    else
        echo -e "${YELLOW}[WARN] El PID registrado no esta ejecutandose${NC}"
        SERVER_RUNNING=false
    fi
else
    echo -e "${YELLOW}[WARN] No se encuentra archivo PID: $PID_FILE${NC}"
    SERVER_RUNNING=false
fi

# Buscar otros procesos del servidor
echo -e "\n${CYAN}--- BUSQUEDA DE PROCESOS ---${NC}"
ALL_PIDS=$(pgrep -f "$SCRIPT_NAME")

if [ -n "$ALL_PIDS" ]; then
    echo -e "${GREEN}[OK] Procesos encontrados: $ALL_PIDS${NC}"
    
    # Si el PID registrado no está ejecutándose pero hay otros procesos
    if [ "$SERVER_RUNNING" = false ]; then
        echo -e "${YELLOW}[WARN] Hay procesos ejecutandose pero no estan registrados en PID file${NC}"
        echo -e "${BLUE}Informacion de procesos encontrados:${NC}"
        for pid in $ALL_PIDS; do
            echo -e "\n${CYAN}--- Proceso PID: $pid ---${NC}"
            get_process_info "$pid"
        done
    fi
else
    echo -e "${RED}[ERROR] No se encontraron procesos del servidor${NC}"
fi

# Verificar archivos de log
echo -e "\n${CYAN}--- ARCHIVOS DE LOG ---${NC}"

if [ -d "$LOG_DIR" ]; then
    echo -e "${GREEN}[OK] Directorio de logs:${NC} $LOG_DIR"
    
    # Listar archivos de log
    LOG_COUNT=$(ls -1 ${LOG_DIR}/LOG_*.txt 2>/dev/null | wc -l)
    if [ "$LOG_COUNT" -gt 0 ]; then
        echo -e "${BLUE}Total de archivos de log:${NC} $LOG_COUNT"
        
        # Mostrar últimos 3 archivos
        echo -e "\n${BLUE}Ultimos archivos de log:${NC}"
        ls -lth ${LOG_DIR}/LOG_*.txt 2>/dev/null | head -3 | awk '{print "   " $9 " (" $5 ")"}'
    else
        echo -e "${YELLOW}[WARN] No se encontraron archivos de log${NC}"
    fi
else
    echo -e "${YELLOW}[WARN] Directorio de logs no existe: $LOG_DIR${NC}"
fi

# Mostrar información del log más reciente
if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
    LOG_SIZE=$(du -h "$LATEST_LOG" | cut -f1)
    LOG_LINES=$(wc -l < "$LATEST_LOG" 2>/dev/null || echo "0")
    LOG_NAME=$(basename "$LATEST_LOG")
    
    echo -e "\n${GREEN}[OK] Log actual:${NC} $LOG_NAME"
    echo -e "   ${BLUE}Tamaño:${NC} $LOG_SIZE"
    echo -e "   ${BLUE}Lineas:${NC} $LOG_LINES"
    
    # Mostrar últimas líneas del log
    echo -e "\n${BLUE}Ultimas 10 lineas del log:${NC}"
    echo -e "${CYAN}---${NC}"
    tail -10 "$LATEST_LOG" | sed 's/^/   /'
    echo -e "${CYAN}---${NC}"
else
    echo -e "\n${YELLOW}[WARN] No se encontro archivo de log actual${NC}"
fi

# Verificar puertos
echo -e "\n${CYAN}--- PUERTOS DE RED ---${NC}"

# Puerto TCP 5003
if netstat -tln 2>/dev/null | grep -q ":5003 "; then
    echo -e "${GREEN}[OK] Puerto TCP 5003:${NC} Escuchando"
else
    echo -e "${RED}[ERROR] Puerto TCP 5003:${NC} No escuchando"
fi

# Verificar conexiones activas
TCP_CONNECTIONS=$(netstat -tn 2>/dev/null | grep ":5003 " | wc -l)
if [ "$TCP_CONNECTIONS" -gt 0 ]; then
    echo -e "${GREEN}[OK] Conexiones TCP activas:${NC} $TCP_CONNECTIONS"
else
    echo -e "${YELLOW}Conexiones TCP activas:${NC} 0"
fi

# Estadísticas del sistema
echo -e "\n${CYAN}--- ESTADISTICAS DEL SISTEMA ---${NC}"
echo -e "${BLUE}Fecha/Hora:${NC} $(date)"
echo -e "${BLUE}Uptime:${NC} $(uptime | awk -F'up ' '{print $2}' | awk -F', load' '{print $1}')"
echo -e "${BLUE}Memoria libre:${NC} $(free -h | awk 'NR==2{printf \"%.1f%%\", $7*100/$2}')"
echo -e "${BLUE}Espacio disco:${NC} $(df -h . | awk 'NR==2{print $4 \" libre de \" $2}')"

# Resumen final
echo -e "\n${CYAN}--- RESUMEN ---${NC}"
if [ "$SERVER_RUNNING" = true ] || [ -n "$ALL_PIDS" ]; then
    echo -e "${GREEN}[OK] Servidor: Ejecutandose${NC}"
    echo -e "${BLUE}Para detener:${NC} ./stop_server_rpg.sh"
else
    echo -e "${RED}[ERROR] Servidor: No ejecutandose${NC}"
    echo -e "${BLUE}Para iniciar:${NC} ./start_server_rpg.sh"
fi

if [ -n "$LATEST_LOG" ]; then
    echo -e "${BLUE}Ver logs en tiempo real:${NC} tail -f $LATEST_LOG"
fi

echo -e "\n${CYAN}--- COMANDOS DISPONIBLES ---${NC}"
echo -e "${YELLOW}Iniciar:${NC} ./start_server_rpg.sh"
echo -e "${YELLOW}Detener:${NC} ./stop_server_rpg.sh"
echo -e "${YELLOW}Estado:${NC} ./server_status_rpg.sh"
if [ -n "$LATEST_LOG" ]; then
    echo -e "${YELLOW}Logs:${NC} tail -f $LATEST_LOG"
fi

echo -e "\n${BLUE}=====================================${NC}"
