#!/bin/bash
# Script para detener el servidor TQ+RPG
# Uso: ./stop_server_rpg.sh

# Configuración
SCRIPT_NAME="tq_server_rpg.py"
PID_FILE="/tmp/tq_server_rpg.pid"
LOG_FILE="tq_server_rpg.log"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 DETENIENDO SERVIDOR TQ+RPG${NC}"
echo "=================================="

# Verificar si existe el archivo PID
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No se encuentra archivo PID: $PID_FILE${NC}"
    echo "   El servidor podría no estar ejecutándose"
    
    # Buscar procesos del servidor por nombre
    echo -e "${BLUE}🔍 Buscando procesos del servidor...${NC}"
    PIDS=$(pgrep -f "$SCRIPT_NAME")
    
    if [ -z "$PIDS" ]; then
        echo -e "${GREEN}✅ No hay procesos del servidor ejecutándose${NC}"
        exit 0
    else
        echo -e "${YELLOW}📋 Procesos encontrados: $PIDS${NC}"
        echo -e "${BLUE}🔄 Intentando detener procesos...${NC}"
        
        # Detener cada proceso encontrado
        for pid in $PIDS; do
            echo -e "   Deteniendo PID: $pid"
            kill -TERM "$pid" 2>/dev/null
            
            # Esperar un momento
            sleep 1
            
            # Verificar si sigue ejecutándose
            if ps -p "$pid" > /dev/null 2>&1; then
                echo -e "   ${YELLOW}Forzando detención de PID: $pid${NC}"
                kill -KILL "$pid" 2>/dev/null
            fi
        done
        
        echo -e "${GREEN}✅ Procesos detenidos${NC}"
        exit 0
    fi
fi

# Leer PID del archivo
PID=$(cat "$PID_FILE")

echo -e "${BLUE}📊 PID del servidor: $PID${NC}"

# Verificar si el proceso existe
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  El proceso PID $PID no existe${NC}"
    echo -e "${BLUE}🧹 Limpiando archivo PID obsoleto${NC}"
    rm -f "$PID_FILE"
    
    # Buscar otros procesos del servidor
    echo -e "${BLUE}🔍 Buscando otros procesos del servidor...${NC}"
    PIDS=$(pgrep -f "$SCRIPT_NAME")
    
    if [ -z "$PIDS" ]; then
        echo -e "${GREEN}✅ No hay procesos del servidor ejecutándose${NC}"
        exit 0
    else
        echo -e "${YELLOW}📋 Otros procesos encontrados: $PIDS${NC}"
        echo -e "${BLUE}🔄 Deteniendo procesos restantes...${NC}"
        
        for pid in $PIDS; do
            echo -e "   Deteniendo PID: $pid"
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            
            if ps -p "$pid" > /dev/null 2>&1; then
                echo -e "   ${YELLOW}Forzando detención de PID: $pid${NC}"
                kill -KILL "$pid" 2>/dev/null
            fi
        done
    fi
else
    # El proceso existe, detenerlo
    echo -e "${BLUE}🔄 Enviando señal TERM al proceso $PID...${NC}"
    kill -TERM "$PID" 2>/dev/null
    
    # Esperar hasta 10 segundos para que termine gracefully
    echo -e "${BLUE}⏳ Esperando detención graceful (máximo 10 segundos)...${NC}"
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Servidor detenido correctamente${NC}"
            break
        fi
        echo -e "   Esperando... ($i/10)"
        sleep 1
    done
    
    # Si aún existe, forzar detención
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Forzando detención del proceso $PID${NC}"
        kill -KILL "$PID" 2>/dev/null
        sleep 1
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${RED}❌ Error: No se pudo detener el proceso $PID${NC}"
            exit 1
        else
            echo -e "${GREEN}✅ Servidor detenido forzadamente${NC}"
        fi
    fi
fi

# Limpiar archivo PID
rm -f "$PID_FILE"

# Verificar que no queden procesos
echo -e "${BLUE}🔍 Verificando que no queden procesos...${NC}"
REMAINING_PIDS=$(pgrep -f "$SCRIPT_NAME")

if [ -z "$REMAINING_PIDS" ]; then
    echo -e "${GREEN}✅ Servidor completamente detenido${NC}"
    echo ""
    echo -e "${GREEN}🎯 RESUMEN:${NC}"
    echo -e "   ${BLUE}📁 PID File:${NC} Eliminado"
    echo -e "   ${BLUE}📁 Log File:${NC} $LOG_FILE (conservado)"
    echo -e "   ${BLUE}🔄 Para reiniciar:${NC} ./start_server_rpg.sh"
else
    echo -e "${YELLOW}⚠️  Quedan procesos del servidor: $REMAINING_PIDS${NC}"
    echo -e "   ${YELLOW}Para detenerlos manualmente:${NC} kill -9 $REMAINING_PIDS"
fi
