#!/bin/bash
# Script para iniciar el servidor TQ+RPG en modo daemon en Ubuntu

echo "🚀 INICIANDO SERVIDOR TQ+RPG EN MODO DAEMON"
echo "=============================================="

# Verificar que Python esté instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 no está instalado"
    exit 1
fi

# Verificar que el archivo del servidor existe
if [ ! -f "tq_server_rpg.py" ]; then
    echo "❌ Error: No se encuentra tq_server_rpg.py"
    exit 1
fi

# Verificar si ya hay un servidor ejecutándose
if pgrep -f "tq_server_rpg.py" > /dev/null; then
    echo "⚠️  Ya hay un servidor ejecutándose"
    echo "   Para detenerlo: ./stop_server.sh"
    echo "   Para ver el proceso: ps aux | grep tq_server_rpg.py"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Iniciar servidor en modo daemon
echo "🔄 Iniciando servidor en segundo plano..."
nohup python3 tq_server_rpg.py --daemon > logs/server.log 2>&1 &

# Obtener el PID del proceso
SERVER_PID=$!

# Esperar un momento para verificar que se inició correctamente
sleep 2

# Verificar si el proceso está ejecutándose
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ Servidor iniciado exitosamente con PID: $SERVER_PID"
    echo "📡 Puerto TCP: 5003"
    echo "📡 Puerto UDP: 7007"
    echo "📋 Logs: logs/server.log"
    echo ""
    echo "🔧 COMANDOS ÚTILES:"
    echo "   Ver logs en tiempo real: tail -f logs/server.log"
    echo "   Ver estado del proceso: ps aux | grep tq_server_rpg.py"
    echo "   Detener servidor: ./stop_server.sh"
    echo "   Verificar puertos: netstat -tlnp | grep :5003"
else
    echo "❌ Error: No se pudo iniciar el servidor"
    echo "   Revisar logs: cat logs/server.log"
    exit 1
fi
