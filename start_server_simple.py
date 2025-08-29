#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple para iniciar el servidor TQ
"""

import sys
import os
from tq_server import TQServer
import threading
import time

def main():
    """Inicia el servidor TQ de manera simple"""
    print("🚀 Iniciando servidor TQ...")
    print("📡 Puerto: 5003")
    print("🌐 Host: 0.0.0.0 (todas las interfaces)")
    print("=" * 50)
    
    # Crear servidor
    server = TQServer(host='0.0.0.0', port=5003)
    
    try:
        # Iniciar servidor
        server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupción detectada...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        server.stop()
        print("👋 Servidor cerrado")

if __name__ == "__main__":
    main()
