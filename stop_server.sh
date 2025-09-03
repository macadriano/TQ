#!/bin/bash
# Script para detener el servidor TQ+RPG

echo "🛑 DETENIENDO SERVIDOR TQ+RPG"
echo "=============================="

# Buscar procesos del servidor
PIDS=$(pgrep -f "tq_server_rpg.py")

if [ -z "$PIDS" ]; then
    echo "ℹ️  No hay servidores ejecutándose"
    exit 0
fi

echo "🔍 Procesos encontrados: $PIDS"

# Detener cada proceso
for PID in $PIDS; do
    echo "🔄 Deteniendo proceso PID: $PID"
    kill -TERM $PID
    
    # Esperar a que se detenga
    sleep 2
    
    # Verificar si se detuvo
    if kill -0 $PID 2>/dev/null; then
        echo "⚠️  Proceso $PID no se detuvo, forzando..."
        kill -KILL $PID
        sleep 1
    fi
    
    # Verificación final
    if kill -0 $PID 2>/dev/null; then
        echo "❌ Error: No se pudo detener proceso $PID"
    else
        echo "✅ Proceso $PID detenido exitosamente"
    fi
done

# Verificación final
REMAINING=$(pgrep -f "tq_server_rpg.py")
if [ -z "$REMAINING" ]; then
    echo ""
    echo "✅ Todos los servidores han sido detenidos"
    echo "🔍 Verificar: ps aux | grep tq_server_rpg.py"
else
    echo ""
    echo "⚠️  Quedan procesos activos: $REMAINING"
    echo "   Para forzar detención: sudo pkill -9 -f tq_server_rpg.py"
fi
