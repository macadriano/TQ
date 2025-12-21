#!/bin/bash
# Script para limpiar logs antiguos
# Uso: ./cleanup_logs.sh [días_a_mantener]
# Por defecto mantiene 30 días de logs

DAYS=${1:-30}

echo "🧹 Iniciando limpieza de logs..."
echo "📅 Manteniendo últimos $DAYS días"
echo ""

python3 cleanup_logs.py $DAYS

echo ""
echo "✅ Script de limpieza finalizado"
