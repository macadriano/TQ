#!/bin/bash
# Script para iniciar el servidor TQ simplificado

echo "🚀 INICIANDO SERVIDOR TQ SIMPLIFICADO"
echo "====================================="
echo ""
echo "📋 Configuración:"
echo "   - Puerto TCP: 5003"
echo "   - Reenvío UDP a: 179.43.115.190:7007"
echo "   - Solo protocolo TQ (cualquier ID)"
echo "   - Rechaza NMEA0183"
echo ""
echo "📁 Archivos de log:"
echo "   - tq_server_simplificado.log"
echo "   - positions_log.csv"
echo "   - rpg_messages.log"
echo ""
echo "⏹️  Para detener: Ctrl+C o ./stop_server_simplificado.sh"
echo ""

# Verificar si ya está ejecutándose
EXISTING=$(pgrep -f "tq_server_simplificado.py")
if [ ! -z "$EXISTING" ]; then
    echo "⚠️  El servidor ya está ejecutándose (PID: $EXISTING)"
    echo "   Para detener: ./stop_server_simplificado.sh"
    echo "   Para ver estado: ./server_status_simplificado.sh"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Iniciar el servidor
echo "🔄 Iniciando servidor..."
python tq_server_simplificado.py
