#!/bin/bash
# Script para verificar el estado del servidor TQ+RPG

echo "📊 ESTADO DEL SERVIDOR TQ+RPG"
echo "=============================="

# Buscar procesos del servidor
PIDS=$(pgrep -f "tq_server_rpg.py")

if [ -z "$PIDS" ]; then
    echo "❌ Servidor NO está ejecutándose"
    echo ""
    echo "🚀 Para iniciarlo: ./start_server_daemon.sh"
    exit 1
fi

echo "✅ Servidor ejecutándose"
echo ""

# Mostrar información de cada proceso
for PID in $PIDS; do
    echo "🆔 Proceso PID: $PID"
    
    # Información del proceso
    PROCESS_INFO=$(ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem --no-headers 2>/dev/null)
    if [ ! -z "$PROCESS_INFO" ]; then
        echo "   Información: $PROCESS_INFO"
    fi
    
    # Verificar puertos
    echo "   🔍 Verificando puertos..."
    
    # Puerto TCP 5003
    TCP_STATUS=$(netstat -tlnp 2>/dev/null | grep ":5003" | head -1)
    if [ ! -z "$TCP_STATUS" ]; then
        echo "   ✅ TCP 5003: Activo"
    else
        echo "   ❌ TCP 5003: Inactivo"
    fi
    
    # Puerto UDP 7007
    UDP_STATUS=$(netstat -ulnp 2>/dev/null | grep ":7007" | head -1)
    if [ ! -z "$UDP_STATUS" ]; then
        echo "   ✅ UDP 7007: Activo"
    else
        echo "   ❌ UDP 7007: Inactivo"
    fi
    
    echo ""
done

# Mostrar logs recientes
if [ -f "logs/server.log" ]; then
    echo "📋 ÚLTIMAS LÍNEAS DEL LOG:"
    echo "============================"
    tail -10 logs/server.log
    echo ""
    echo "📖 Para ver logs completos: tail -f logs/server.log"
else
    echo "📋 No se encontraron logs del servidor"
fi

echo ""
echo "🔧 COMANDOS ÚTILES:"
echo "   Detener servidor: ./stop_server.sh"
echo "   Reiniciar servidor: ./stop_server.sh && ./start_server_daemon.sh"
echo "   Ver procesos: ps aux | grep tq_server_rpg.py"
echo "   Ver puertos: netstat -tlnp | grep :5003"
