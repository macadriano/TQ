#!/bin/bash
# Script para verificar el estado del servidor TQ+RPG
# Uso: ./server_status_rpg.sh

# Configuración
SCRIPT_NAME="tq_server_rpg.py"
PID_FILE="/tmp/tq_server_rpg.pid"
LOG_FILE="tq_server_rpg.log"
POSITIONS_FILE="positions_log.csv"
RPG_LOG_FILE="rpg_messages.log"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 ESTADO DEL SERVIDOR TQ+RPG${NC}"
echo "=================================="

# Función para obtener información del proceso
get_process_info() {
    local pid=$1
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        # Información básica del proceso
        local cmd=$(ps -p "$pid" -o cmd= 2>/dev/null | tr -d '\n')
        local start_time=$(ps -p "$pid" -o lstart= 2>/dev/null | tr -d '\n')
        local cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | tr -d ' ')
        local mem=$(ps -p "$pid" -o %mem= 2>/dev/null | tr -d ' ')
        
        echo -e "   ${GREEN}✅ Estado:${NC} Ejecutándose"
        echo -e "   ${BLUE}📊 PID:${NC} $pid"
        echo -e "   ${BLUE}🕐 Iniciado:${NC} $start_time"
        echo -e "   ${BLUE}💻 CPU:${NC} ${cpu}%"
        echo -e "   ${BLUE}💾 Memoria:${NC} ${mem}%"
        echo -e "   ${BLUE}📝 Comando:${NC} $cmd"
        return 0
    else
        echo -e "   ${RED}❌ Estado:${NC} No ejecutándose"
        return 1
    fi
}

# Verificar archivo PID
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo -e "${BLUE}📁 Archivo PID encontrado: $PID_FILE${NC}"
    echo -e "${BLUE}📊 PID registrado: $PID${NC}"
    
    if get_process_info "$PID"; then
        SERVER_RUNNING=true
    else
        echo -e "${YELLOW}⚠️  El PID registrado no está ejecutándose${NC}"
        SERVER_RUNNING=false
    fi
else
    echo -e "${YELLOW}⚠️  No se encuentra archivo PID: $PID_FILE${NC}"
    SERVER_RUNNING=false
fi

# Buscar otros procesos del servidor
echo -e "\n${BLUE}🔍 Buscando procesos del servidor...${NC}"
ALL_PIDS=$(pgrep -f "$SCRIPT_NAME")

if [ -n "$ALL_PIDS" ]; then
    echo -e "${GREEN}📋 Procesos encontrados: $ALL_PIDS${NC}"
    
    # Si el PID registrado no está ejecutándose pero hay otros procesos
    if [ "$SERVER_RUNNING" = false ]; then
        echo -e "${YELLOW}⚠️  Hay procesos ejecutándose pero no están registrados en PID file${NC}"
        echo -e "${BLUE}🔄 Información de procesos encontrados:${NC}"
        for pid in $ALL_PIDS; do
            echo -e "\n${CYAN}--- Proceso PID: $pid ---${NC}"
            get_process_info "$pid"
        done
    fi
else
    echo -e "${RED}❌ No se encontraron procesos del servidor${NC}"
fi

# Verificar archivos de log
echo -e "\n${BLUE}📁 ARCHIVOS DE LOG:${NC}"

if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
    LOG_LINES=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
    echo -e "   ${GREEN}✅ Log principal:${NC} $LOG_FILE"
    echo -e "      ${BLUE}Tamaño:${NC} $LOG_SIZE"
    echo -e "      ${BLUE}Líneas:${NC} $LOG_LINES"
    
    # Mostrar últimas líneas del log
    echo -e "\n${BLUE}📋 Últimas 5 líneas del log:${NC}"
    tail -5 "$LOG_FILE" | sed 's/^/   /'
else
    echo -e "   ${YELLOW}⚠️  Log principal:${NC} $LOG_FILE (no encontrado)"
fi

if [ -f "$POSITIONS_FILE" ]; then
    POS_SIZE=$(du -h "$POSITIONS_FILE" | cut -f1)
    POS_LINES=$(wc -l < "$POSITIONS_FILE" 2>/dev/null || echo "0")
    echo -e "   ${GREEN}✅ Log posiciones:${NC} $POSITIONS_FILE"
    echo -e "      ${BLUE}Tamaño:${NC} $POS_SIZE"
    echo -e "      ${BLUE}Registros:${NC} $((POS_LINES - 1)) posiciones"
else
    echo -e "   ${YELLOW}⚠️  Log posiciones:${NC} $POSITIONS_FILE (no encontrado)"
fi

if [ -f "$RPG_LOG_FILE" ]; then
    RPG_SIZE=$(du -h "$RPG_LOG_FILE" | cut -f1)
    RPG_LINES=$(wc -l < "$RPG_LOG_FILE" 2>/dev/null || echo "0")
    echo -e "   ${GREEN}✅ Log RPG:${NC} $RPG_LOG_FILE"
    echo -e "      ${BLUE}Tamaño:${NC} $RPG_SIZE"
    echo -e "      ${BLUE}Mensajes:${NC} $RPG_LINES"
else
    echo -e "   ${YELLOW}⚠️  Log RPG:${NC} $RPG_LOG_FILE (no encontrado)"
fi

# Verificar puertos
echo -e "\n${BLUE}🌐 PUERTOS DE RED:${NC}"

# Puerto TCP 5003
if netstat -tln 2>/dev/null | grep -q ":5003 "; then
    echo -e "   ${GREEN}✅ Puerto TCP 5003:${NC} Escuchando"
else
    echo -e "   ${RED}❌ Puerto TCP 5003:${NC} No escuchando"
fi

# Verificar conexiones activas
TCP_CONNECTIONS=$(netstat -tn 2>/dev/null | grep ":5003 " | wc -l)
if [ "$TCP_CONNECTIONS" -gt 0 ]; then
    echo -e "   ${BLUE}📊 Conexiones TCP activas:${NC} $TCP_CONNECTIONS"
else
    echo -e "   ${YELLOW}📊 Conexiones TCP activas:${NC} 0"
fi

# Estadísticas del sistema
echo -e "\n${BLUE}💻 ESTADÍSTICAS DEL SISTEMA:${NC}"
echo -e "   ${BLUE}🕐 Fecha/Hora:${NC} $(date)"
echo -e "   ${BLUE}💻 Uptime:${NC} $(uptime | awk -F'up ' '{print $2}' | awk -F', load' '{print $1}')"
echo -e "   ${BLUE}💾 Memoria libre:${NC} $(free -h | awk 'NR==2{printf "%.1f%%", $7*100/$2}')"
echo -e "   ${BLUE}💽 Espacio disco:${NC} $(df -h . | awk 'NR==2{print $4 " libre de " $2}')"

# Resumen final
echo -e "\n${BLUE}📋 RESUMEN:${NC}"
if [ "$SERVER_RUNNING" = true ] || [ -n "$ALL_PIDS" ]; then
    echo -e "   ${GREEN}✅ Servidor:${NC} Ejecutándose"
    echo -e "   ${BLUE}🔄 Para detener:${NC} ./stop_server_rpg.sh"
else
    echo -e "   ${RED}❌ Servidor:${NC} No ejecutándose"
    echo -e "   ${BLUE}🚀 Para iniciar:${NC} ./start_server_rpg.sh"
fi

echo -e "   ${BLUE}📊 Para ver logs en tiempo real:${NC} tail -f $LOG_FILE"
echo -e "   ${BLUE}📊 Para ver posiciones:${NC} tail -f $POSITIONS_FILE"

echo -e "\n${GREEN}🎯 COMANDOS DISPONIBLES:${NC}"
echo -e "   ${YELLOW}Iniciar:${NC} ./start_server_rpg.sh"
echo -e "   ${YELLOW}Detener:${NC} ./stop_server_rpg.sh"
echo -e "   ${YELLOW}Estado:${NC} ./server_status_rpg.sh"
echo -e "   ${YELLOW}Logs:${NC} tail -f $LOG_FILE"
