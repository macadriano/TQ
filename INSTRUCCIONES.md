

# 🚀 Protocolo TQ - Instrucciones de Uso

## 📋 Configuración Actual

- **Servidor**: `200.58.98.187:5003`
- **Cliente**: Se conecta a `200.58.98.187:5003`
- **Puerto**: 5003

## 🔧 Pasos para Ejecutar

### 1. Iniciar el Servidor

En tu servidor (200.58.98.187), ejecuta:

```bash
# Opción 1: Servidor con interfaz interactiva
python3 tq_server.py

# Opción 2: Servidor simple (recomendado)
python3 start_server_simple.py
```

### 2. Verificar que el Servidor esté Funcionando

En tu servidor, verifica que el puerto 5003 esté abierto:

```bash
sudo ss -ltnp | grep :5003
```

Deberías ver algo como:
```
LISTEN 0 5 0.0.0.0:5003 0.0.0.0:* users:(("python3",pid=XXXX,fd=3))
```

### 3. Probar la Conexión

En tu máquina local, ejecuta el script de prueba:

```bash
python test_connection.py
```

### 4. Ejecutar el Cliente

Si la prueba es exitosa, ejecuta el cliente completo:

```bash
python tq_client_test.py
```

## 🛠️ Solución de Problemas

### Error: "Address already in use"

**Causa**: El puerto 5003 ya está siendo usado por otro proceso.

**Solución**:
1. Verificar qué proceso usa el puerto:
   ```bash
   sudo ss -ltnp | grep :5003
   ```

2. Terminar el proceso si es necesario:
   ```bash
   sudo kill -9 <PID>
   ```

### Error: "Connection refused"

**Causa**: El servidor no está ejecutándose o el firewall bloquea el puerto.

**Solución**:
1. Verificar que el servidor esté ejecutándose
2. Verificar el firewall:
   ```bash
   sudo ufw status
   sudo ufw allow 5003
   ```

### Error: "Timeout"

**Causa**: Problemas de red o firewall.

**Solución**:
1. Verificar conectividad:
   ```bash
   ping 200.58.98.187
   telnet 200.58.98.187 5003
   ```

## 📁 Archivos del Sistema

- `tq_server.py` - Servidor principal con interfaz interactiva
- `start_server_simple.py` - Servidor simple sin interfaz
- `tq_client_test.py` - Cliente de prueba
- `test_connection.py` - Script de prueba de conexión
- `tq_server.log` - Log del servidor (se crea automáticamente)

## 🔄 Flujo de Datos

1. **Cliente** → Envía mensajes de posición al servidor
2. **Servidor** → Recibe y decodifica los mensajes
3. **Servidor** → Muestra la información en pantalla y la guarda en log

## 📊 Formatos de Mensaje Soportados

1. **Binario** (struct) - Formato compacto
2. **Texto** - Con delimitadores (coma)
3. **Hexadecimal** - Formato hex

## 🎯 Próximos Pasos

1. ✅ Configurar puerto 5003
2. ✅ Probar conexión básica
3. ✅ Ejecutar cliente y servidor
4. 🔄 Adaptar protocolo según PDF específico
5. 🔄 Implementar base de datos
6. 🔄 Crear interfaz web
