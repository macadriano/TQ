#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demostración del sistema de logging optimizado
Muestra la diferencia entre logging verbose y optimizado
"""

from log_optimizer import get_rpg_logger
from datetime import datetime

def demo_verbose_logging():
    """Simula el logging verbose actual"""
    print("=" * 80)
    print("📝 LOGGING VERBOSE (ACTUAL)")
    print("=" * 80)
    print()
    
    verbose_log = """2025-12-03 10:11:45 - INFO - Msg #5979 de 186.12.40.83:48013: 2491765959991...
2025-12-03 10:11:45 - INFO - Tipo de protocolo detectado: 59
2025-12-03 10:11:45 - INFO - Protocolo 59 - intentando decodificación TQ
2025-12-03 10:11:45 - INFO - Coordenadas hexadecimales extraídas: Lat=-40.772199°, Lon=-71.607830°
2025-12-03 10:11:45 - INFO - Velocidad y rumbo extraídos: 0.0 km/h, Rumbo: 119°
2025-12-03 10:11:45 - INFO - Posición decodificada: {'device_id': '95999', 'device_id_completo': '9176595999', 'latitude': -40.772199, 'longitude': -71.607830, 'heading': 119, 'speed': 0, 'fecha_gps': '03/12/25', 'hora_gps': '12:02:50', 'timestamp': '2025-12-03T10:11:45.123456'}
2025-12-03 10:11:45 - INFO - Usando fecha/hora GPS original: 03/12/25 12:02:50 UTC (sin offset)
2025-12-03 10:11:45 - INFO - Mensaje RPG creado desde GPS: >RGP031225120250-4046.3319-07136.4698000119000001;&01;ID=95999;#0001*62<
2025-12-03 10:11:45 - INFO - Datos reenviados por TCP a 200.58.98.187:5003
2025-12-03 10:11:45 - INFO - Mensaje enviado correctamente.
2025-12-03 10:11:45 - INFO - Mensaje RPG loggeado: ENVIADO_RPG_GPS"""
    
    print(verbose_log)
    print()
    print(f"📊 Tamaño aproximado: {len(verbose_log)} caracteres")
    print()

def demo_optimized_logging():
    """Simula el logging optimizado"""
    print("=" * 80)
    print("✨ LOGGING OPTIMIZADO (NUEVO)")
    print("=" * 80)
    print()
    
    optimized_log = """2025-12-03 10:11:45 - Protocolo: 59
GPS: ID=95999, LAT=-40.772199, LON=-71.607830, RUMBO=119, VEL=0 km/h
Timestamp GPS: 03/12/25 12:02:50 UTC
Envío UDP: 179.43.115.190:7007 - >RGP031225120250-4046.3319-07136.4698000119000001;&01;ID=95999;#0001*62<
Envío TCP: 200.58.98.187:5003 - 24917659599912491765959991244210312253404633190713646980000000...
--------------------------------------------------------------------------------"""
    
    print(optimized_log)
    print()
    print(f"📊 Tamaño aproximado: {len(optimized_log)} caracteres")
    print()

def demo_comparison():
    """Muestra la comparación de tamaños"""
    print("=" * 80)
    print("📊 COMPARACIÓN DE EFICIENCIA")
    print("=" * 80)
    print()
    
    verbose_size = 1024  # Ejemplo: 1 KB por evento
    optimized_size = 310  # Ejemplo: 310 bytes por evento
    reduction = ((verbose_size - optimized_size) / verbose_size) * 100
    
    print(f"Tamaño por evento (verbose):    {verbose_size:,} bytes (~1.0 KB)")
    print(f"Tamaño por evento (optimizado): {optimized_size:,} bytes (~0.3 KB)")
    print(f"Reducción de espacio:           {reduction:.1f}%")
    print()
    
    # Proyección para 1000 eventos
    events = 10000
    verbose_total = (verbose_size * events) / (1024 * 1024)  # MB
    optimized_total = (optimized_size * events) / (1024 * 1024)  # MB
    saved = verbose_total - optimized_total
    
    print(f"Proyección para {events:,} eventos por día:")
    print(f"  Verbose:    {verbose_total:.2f} MB/día")
    print(f"  Optimizado: {optimized_total:.2f} MB/día")
    print(f"  Ahorro:     {saved:.2f} MB/día ({saved * 30:.2f} MB/mes)")
    print()

def demo_cleanup():
    """Demuestra la funcionalidad de limpieza"""
    print("=" * 80)
    print("🧹 DEMOSTRACIÓN DE LIMPIEZA AUTOMÁTICA")
    print("=" * 80)
    print()
    
    cleanup_output = """🧹 Limpiando logs antiguos...
🗑️  Log eliminado: LOG_151125.txt (245.32 KB, 2025-11-15)
🗑️  Log eliminado: LOG_161125.txt (312.45 KB, 2025-11-16)
🗑️  Log eliminado: RPG_151125.txt (89.15 KB, 2025-11-15)
🗑️  Log eliminado: RPG_161125.txt (102.87 KB, 2025-11-16)
✅ Limpieza completada: 4 archivo(s) eliminado(s), 0.73 MB liberados"""
    
    print(cleanup_output)
    print()
    print("✅ Los logs se limpian automáticamente al iniciar el servidor")
    print("✅ Solo se mantienen los últimos 15 días")
    print("✅ También se puede ejecutar manualmente: ./cleanup_logs.sh")
    print()

def main():
    """Función principal de demostración"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "SISTEMA DE LOGGING OPTIMIZADO" + " " * 29 + "║")
    print("║" + " " * 25 + "Demostración Interactiva" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    # Mostrar logging verbose
    demo_verbose_logging()
    input("Presiona ENTER para ver el logging optimizado...")
    print("\n")
    
    # Mostrar logging optimizado
    demo_optimized_logging()
    input("Presiona ENTER para ver la comparación...")
    print("\n")
    
    # Mostrar comparación
    demo_comparison()
    input("Presiona ENTER para ver la limpieza automática...")
    print("\n")
    
    # Mostrar limpieza
    demo_cleanup()
    
    print()
    print("=" * 80)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("=" * 80)
    print()
    print("Para más información, consulta: README_LOG_OPTIMIZER.md")
    print()

if __name__ == "__main__":
    main()
