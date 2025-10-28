#!/bin/bash
# Script para iniciar el servidor TQ+RPG en segundo plano
# Uso: ./start_server_rpg.sh

# Configuración
SCRIPT_NAME="tq_server_rpg.py"
PID_FILE="/tmp/tq_server_rpg.pid"
LOG_FILE="tq_server_rpg.log"
PYTHON_CMD="python3"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 INICIANDO SERVIDOR TQ+RPG${NC}"
echo "=================================="

# Verificar si el script existe
if [ ! -f "$SCRIPT_NAME" ]; then
    echo -e "${RED}❌ Error: No se encuentra el archivo $SCRIPT_NAME${NC}"
    echo "   Asegúrate de estar en el directorio correcto"
    exit 1
fi

# Verificar si ya está ejecutándose
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  El servidor ya está ejecutándose (PID: $PID)${NC}"
        echo "   Para detenerlo: ./stop_server_rpg.sh"
        echo "   Para ver estado: ./server_status_rpg.sh"
        exit 1
    else
        echo -e "${YELLOW}🧹 Limpiando archivo PID obsoleto${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Verificar dependencias
echo -e "${BLUE}📋 Verificando dependencias...${NC}"

# Verificar Python
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo -e "${RED}❌ Error: Python3 no está instalado${NC}"
    exit 1
fi

# Verificar módulos Python necesarios
python3 -c "import socket, threading, logging, csv, os, math, requests, time, datetime" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Faltan módulos Python necesarios${NC}"
    echo "   Instala las dependencias: pip3 install requests"
    exit 1
fi

# Verificar archivos de módulos
if [ ! -f "funciones.py" ] || [ ! -f "protocolo.py" ]; then
    echo -e "${RED}❌ Error: Faltan archivos de módulos (funciones.py, protocolo.py)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dependencias verificadas${NC}"

# Crear directorio de logs si no existe
mkdir -p logs

# Iniciar servidor en segundo plano
echo -e "${BLUE}🔄 Iniciando servidor en segundo plano...${NC}"

# Ejecutar con nohup para que persista después de cerrar terminal
nohup "$PYTHON_CMD" "$SCRIPT_NAME" --daemon > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Guardar PID
echo "$SERVER_PID" > "$PID_FILE"

# Esperar un momento para verificar que inició correctamente
sleep 2

# Verificar que el proceso sigue ejecutándose
if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Servidor iniciado correctamente${NC}"
    echo -e "   ${BLUE}📊 PID:${NC} $SERVER_PID"
    echo -e "   ${BLUE}📁 Log:${NC} $LOG_FILE"
    echo -e "   ${BLUE}📁 PID File:${NC} $PID_FILE"
    echo ""
    echo -e "${GREEN}🎯 COMANDOS DISPONIBLES:${NC}"
    echo -e "   ${YELLOW}Ver estado:${NC} ./server_status_rpg.sh"
    echo -e "   ${YELLOW}Detener:${NC} ./stop_server_rpg.sh"
    echo -e "   ${YELLOW}Ver logs:${NC} tail -f $LOG_FILE"
    echo ""
    echo -e "${BLUE}📡 Servidor escuchando en puerto 5003${NC}"
    echo -e "${BLUE}📡 UDP configurado para reenvío a 179.43.115.190:7007${NC}"
else
    echo -e "${RED}❌ Error: El servidor no pudo iniciarse${NC}"
    echo -e "   ${YELLOW}Revisa el log:${NC} cat $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
