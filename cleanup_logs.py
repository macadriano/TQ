#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar logs antiguos manualmente
Elimina archivos de log más antiguos que el número de días especificado
"""

import sys
import os

# Agregar el directorio actual al path para importar funciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import funciones

def main():
    """Función principal para limpieza de logs"""
    print("=" * 60)
    print("LIMPIEZA DE LOGS ANTIGUOS")
    print("=" * 60)
    
    # Configuración por defecto
    days_to_keep = 30
    log_dir = "logs"
    
    # Permitir especificar días como argumento
    if len(sys.argv) > 1:
        try:
            days_to_keep = int(sys.argv[1])
            print(f"Dias a mantener (personalizado): {days_to_keep}")
        except ValueError:
            print(f"⚠️  Argumento inválido, usando valor por defecto: {days_to_keep} días")
    else:
        print(f"Dias a mantener (por defecto): {days_to_keep}")
    
    print(f"Directorio de logs: {log_dir}/")
    print()
    
    # Ejecutar limpieza
    stats = funciones.cleanup_old_logs(days_to_keep=days_to_keep, log_dir=log_dir)
    
    # Mostrar resumen
    print()
    print("=" * 60)
    print("RESUMEN DE LIMPIEZA")
    print("=" * 60)
    print(f"Archivos eliminados: {stats['deleted_count']}")
    print(f"Espacio liberado: {stats['size_freed_mb']} MB ({stats['size_freed_bytes']} bytes)")
    print(f"Fecha límite: {stats['cutoff_date']}")
    print(f"Días mantenidos: {stats['days_kept']}")
    
    if stats.get('error'):
        print(f"Error: {stats['error']}")
    
    if stats['deleted_files']:
        print()
        print("Archivos eliminados:")
        for filename in stats['deleted_files']:
            print(f"  - {filename}")
    
    print()
    print("Limpieza completada")

if __name__ == "__main__":
    main()
