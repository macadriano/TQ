# 🚀 SERVIDOR TQ+RPG - MODO DAEMON PARA UBUNTU

## 📋 **PROBLEMA IDENTIFICADO**

Cuando intentas ejecutar el servidor en segundo plano en Ubuntu usando `&`, el proceso se detiene automáticamente porque está esperando input del usuario (bucle de comandos interactivo).

## ✅ **SOLUCIÓN IMPLEMENTADA**

He modificado el servidor para soportar **modo daemon** que permite ejecutarse en segundo plano sin problemas.

## 🔧 **ARCHIVOS CREADOS**

- `start_server_daemon.sh` - Script para iniciar el servidor en modo daemon
- `stop_server.sh` - Script para detener el servidor
- `server_status.sh` - Script para verificar el estado del servidor

## 🚀 **INSTRUCCIONES DE USO**

### **1. Hacer ejecutables los scripts**
```bash
chmod +x start_server_daemon.sh stop_server.sh server_status.sh
```

### **2. Iniciar servidor en modo daemon**
```bash
./start_server_daemon.sh
```

**Resultado esperado:**
```
🚀 INICIANDO SERVIDOR TQ+RPG EN MODO DAEMON
==============================================
🔄 Iniciando servidor en segundo plano...
✅ Servidor iniciado exitosamente con PID: 12345
📡 Puerto TCP: 5003
📡 Puerto UDP: 7007
📋 Logs: logs/server.log
```

### **3. Verificar estado del servidor**
```bash
./server_status.sh
```

### **4. Ver logs en tiempo real**
```bash
tail -f logs/server.log
```

### **5. Detener servidor**
```bash
./stop_server.sh
```

## 🔍 **VERIFICACIONES MANUALES**

### **Verificar proceso activo:**
```bash
ps aux | grep tq_server_rpg.py
```

### **Verificar puertos activos:**
```bash
netstat -tlnp | grep :5003
netstat -ulnp | grep :7007
```

### **Verificar logs:**
```bash
cat logs/server.log
```

## 🆚 **COMPARACIÓN DE MODOS**

### **Modo Interactivo (Original):**
```bash
python3 tq_server_rpg.py
# ✅ Funciona pero requiere terminal activa
# ❌ Se detiene si cierras la terminal
```

### **Modo Daemon (Nuevo):**
```bash
python3 tq_server_rpg.py --daemon
# ✅ Ejecuta en segundo plano
# ✅ No requiere terminal activa
# ✅ Continúa ejecutándose después de cerrar terminal
```

### **Modo Daemon con Script:**
```bash
./start_server_daemon.sh
# ✅ Inicio automático con verificaciones
# ✅ Logs organizados
# ✅ Fácil gestión del proceso
```

## 🚨 **COMANDOS DE EMERGENCIA**

### **Forzar detención (si stop_server.sh falla):**
```bash
sudo pkill -9 -f tq_server_rpg.py
```

### **Reiniciar servidor:**
```bash
./stop_server.sh && ./start_server_daemon.sh
```

### **Ver todos los procesos relacionados:**
```bash
ps aux | grep -E "(tq_server|python.*tq)"
```

## 📁 **ESTRUCTURA DE LOGS**

```
logs/
└── server.log          # Log principal del servidor
tq_server_rpg.log       # Log interno del servidor
positions_log.csv       # Posiciones GPS recibidas
rpg_messages.log        # Mensajes RPG enviados
```

## 🔧 **CONFIGURACIÓN AVANZADA**

### **Cambiar puertos (editar start_server_daemon.sh):**
```bash
# Puerto TCP (línea 35)
nohup python3 tq_server_rpg.py --daemon > logs/server.log 2>&1 &
```

### **Ejecutar en puerto específico:**
```bash
# Modificar tq_server_rpg.py línea 608
server = TQServerRPG(host='0.0.0.0', port=5004, 
                     udp_host='179.43.115.190', udp_port=7008)
```

## ✅ **VENTAJAS DEL MODO DAEMON**

1. **🔄 Ejecución continua** - No se detiene al cerrar terminal
2. **📋 Logs organizados** - Todos los logs van a archivos
3. **🔍 Fácil monitoreo** - Scripts para gestión completa
4. **🚀 Inicio automático** - Verificaciones automáticas
5. **🛑 Parada controlada** - Detención limpia del proceso

## 🎯 **RESULTADO FINAL**

Con esta implementación, podrás:
- ✅ Ejecutar el servidor en segundo plano sin problemas
- ✅ Cerrar la terminal sin que se detenga el servidor
- ✅ Monitorear el estado fácilmente
- ✅ Gestionar logs de forma organizada
- ✅ Detener/reiniciar el servidor de forma controlada

El servidor ahora funcionará perfectamente en Ubuntu como un servicio en segundo plano. 🚀
