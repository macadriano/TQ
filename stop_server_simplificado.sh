#!/bin/bash
# Script para detener el servidor TQ simplificado

echo "🛑 DETENIENDO SERVIDOR TQ SIMPLIFICADO"
echo "======================================"

# Buscar procesos del servidor
PIDS=$(pgrep -f "tq_server_simplificado.py")

if [ -z "$PIDS" ]; then
    echo "ℹ️  No hay servidores simplificados ejecutándose"
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
REMAINING=$(pgrep -f "tq_server_simplificado.py")
if [ -z "$REMAINING" ]; then
    echo ""
    echo "✅ Todos los servidores simplificados han sido detenidos"
    echo "🔍 Verificar: ps aux | grep tq_server_simplificado.py"
else
    echo ""
    echo "⚠️  Quedan procesos activos: $REMAINING"
    echo "   Para forzar detención: sudo pkill -9 -f tq_server_simplificado.py"
fi

echo ""
echo "📊 ESTADÍSTICAS FINALES:"
if [ -f "positions_log.csv" ]; then
    POSITION_COUNT=$(wc -l < positions_log.csv)
    echo "   Posiciones registradas: $POSITION_COUNT"
fi
if [ -f "rpg_messages.log" ]; then
    RPG_COUNT=$(wc -l < rpg_messages.log)
    echo "   Mensajes RPG enviados: $RPG_COUNT"
fi
