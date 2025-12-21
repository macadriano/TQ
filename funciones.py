import binascii
import socket
import os
import glob
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

def bytes2hexa(valor_bytes):
#valor_bytes = b'xx\r\x01\x08eF\x80P\x13\x82\x16\x00\xbe\xb9\xfa\r\n'  # Valor en bytes
# Convertir el valor en bytes a hexadecimal
    valor_hexadecimal = binascii.hexlify(valor_bytes).decode()
    return valor_hexadecimal


#print("Valor en bytes:", valor_bytes)
#print("Valor hexadecimal:", valor_hexadecimal)

def hexa2bytes(valor_hexadecimal):
# Convertir la cadena de bytes en valor hexadecimal
# 78780d01086546805013821600beb9fa0d0a
    cadena_bytes = bytes.fromhex(valor_hexadecimal)
    return cadena_bytes

def bytes2string(valor_bytes):
    encoding = 'utf-8'
    # Convierte los bytes a una cadena
    cadena = valor_bytes.decode(encoding)
    return cadena

#valorHexa="78780d01086546805013821600beb9fa0d0a"
#print(hexa2bytes(valorHexa))

#valorBytes = b'xx\r\x01\x08eF\x80P\x13\x82\x16\x00\xbe\xb9\xfa\r\n'
#print(bytes2hexa(valorBytes))

def getID(cadena):
    equipo = cadena[10:18]
    return equipo

"""0x0100:  terminal register
    7E 01 00 00 27 01 38 33 50 42 79 00 13 00 2C 01 2F 37 30 31 31 31 42 53 4A 2D 41 36 2D 42 00 00 00 00 00 00 00 00 00 00 00 33 35 30 34 32 37 39 01 4E 58 63 7E
    7E010000270138335042790013002C012F373031313142534A2D41362D42000000000000000000000033353034323739014E58637E
    0123456789*0123456789*0123456789*0123456789*0123456789*0123456789*0123456789*0123456789*0123456789*0123456789*
    7E 	header
    01 00 	main segnaling
    00 27 	Message Body Length
    01 38 33 50 42 79 	Tracker SN number
    00 13 	Serial Code (number)
    00 2C 	provincial ID
    01 2F 	city ID
    37 30 31 31 31	Manufacturer ID 
    42 53 4A 2D 41 36 2D 42 00 00 00 00 00 00 00 00 00 00 00 	terminal type
    33 35 30 34 32 37 39 	terminal ID (The factory default)
    01 	plate color
    4E 58 	plate
    63 	checksum
    7E	Ending
    """

def get_daily_log_filename():
    """
    Genera el nombre de archivo de log diario con formato logs/LOG_DDMMYY.txt
    Crea la carpeta logs/ si no existe
    """
    # Crear carpeta logs/ si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Obtener fecha actual en formato DDMMYY
    now = datetime.now()
    fecha_str = now.strftime('%d%m%y')  # DDMMYY
    
    # Construir nombre de archivo único para todo
    filename = f"logs/LOG_{fecha_str}.txt"
    return filename

def guardarLog(cadena):
    """Guarda un mensaje en el log diario único"""
    archivo_path = get_daily_log_filename()
    archivo = open(archivo_path, "a", encoding='utf-8')
    fechaHora = getFechaHora()
    archivo.write(fechaHora + ": " + cadena + "\n")
    archivo.close()

def guardarLogArchivo(cadena, tag=""):
    """
    Guarda log en el archivo diario único con un tag opcional
    El tag permite identificar el tipo de mensaje
    """
    archivo_path = get_daily_log_filename()
    archivo = open(archivo_path, "a", encoding='utf-8')
    fechaHora = getFechaHora()
    if tag:
        archivo.write(fechaHora + f" [{tag}]: " + cadena + "\n")
    else:
        archivo.write(fechaHora + ": " + cadena + "\n")
    archivo.close()	
	
def guardarLogPersonal(cadena):
    """Guarda log personal en el archivo diario único con tag [PERSONAL]"""
    guardarLogArchivo(cadena, "PERSONAL")

def guardarLogUDP(cadena):
    """Guarda log UDP en el archivo diario único con tag [UDP]"""
    guardarLogArchivo(cadena, "UDP")

def guardarLogNMEA(cadena):
    """Guarda log NMEA en el archivo diario único con tag [NMEA]"""
    guardarLogArchivo(cadena, "NMEA")

def getFechaHora():
    # Obtener componentes individuales de la fecha y hora
    fecha_hora_actual = datetime.now()
    anio = fecha_hora_actual.year
    mes = fecha_hora_actual.month
    dia = fecha_hora_actual.day
    hora = fecha_hora_actual.hour
    minutos = fecha_hora_actual.minute
    segundos = fecha_hora_actual.second

    # Imprimir la fecha como una cadena de texto
    return str(dia) + "/" + str(mes) + "/" + str(anio) + " " + str(hora) + ":" + str(minutos) + ":" + str(segundos)

def enviar_mensaje_udp(ip_destino, puerto_destino, mensaje):
    # Crear un socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Enviar el mensaje al destino
        sock.sendto(mensaje.encode(), (ip_destino, puerto_destino))
        print("Mensaje enviado correctamente.")
        # guardando datos en archivo de LOG
        guardarLog(getFechaHora() + " --> " + mensaje)

    except Exception as e:
        print("Error al enviar el mensaje:", str(e))
        # guardando datos en archivo de LOG
        guardarLog("Error al enviar el mensaje UDP:", str(e))
    finally:
        # Cerrar el socket
        sock.close()


def calcular_crc(data):
    crc = 0xFFFF  # Valor inicial del CRC

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1

    return crc
"""
# Datos de ejemplo
datos = b"123456789"

# Calcular el CRC-ITU checksum
checksum = calcular_crc(datos)

# Imprimir el resultado en formato hexadecimal
print(hex(checksum))
"""

def calcular_crcITU(data):
    crc = 0xFFFF  # Valor inicial del CRC-ITU
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    crc = crc.to_bytes(2, byteorder='big')
    crc = binascii.hexlify(crc).decode('utf-8').upper()
    return crc

def calcular_crcV2(data):
    crc = 0xFFFF  # Valor inicial del CRC-ITU
    data_bytes = binascii.unhexlify(data)  # Convertir cadena hexadecimal a bytes
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    crc = crc.to_bytes(2, byteorder='big')
    crc = binascii.hexlify(crc).decode('utf-8').upper()
    return crc

def calcular_checksum(data):
    checksum = sum(data) & 0xFFFF
    checksum = hex(checksum)[2:].upper().zfill(4)
    return checksum

def hexa_a_decimal(hexadecimal):
    decimal = int(hexadecimal, 16)
    return decimal

def completaCero(dato):
    if len(dato) == 1:
        return "0" + dato
    else:
        return dato
    
def completaCero3(dato):
    xdato = str(dato)
    if len(xdato) == 1:
        return "00" + xdato
    elif len(xdato) == 2:
        return "0" + xdato
    else:
        return xdato

def crc_itu(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF  # Asegura que el CRC se mantenga en 16 bits
    return crc

# Ejemplo de uso:
# data = b"123456789"
# crc_value = crc_itu(data)
# print(f"CRC-ITU: {crc_value:04X}")

def AjustarUTC(fecha_hora,ajuste):
    # Realizar "ajuste" horas a un objeto datetime
    # fecha_hora = datetime(2024, 2, 15, 12, 6, 32)
    print(ajuste)
    diferencia = timedelta(hours=ajuste)
    nueva_fecha_hora = fecha_hora + diferencia
    print(nueva_fecha_hora)
    # 2024-02-15 09:06:32
    return nueva_fecha_hora

def AcomodarFecha(fecha):
    # Realizar transformaciones de formatos fecha y AjusteUTC
    fecha_hora = datetime(int(fecha[4:6]), int(fecha[2:4]), int(fecha[0:2]), int(fecha[6:8]), int(fecha[8:10]), int(fecha[10:12]))
    nueva_fecha_hora = AjustarUTC(fecha_hora,(-3))
    str_fecha_hora = str(nueva_fecha_hora.year) + "/" + str(nueva_fecha_hora.month) + "/" + str(nueva_fecha_hora.day) + " " + str(nueva_fecha_hora.hour) + ":" + str(nueva_fecha_hora.minute) + ":" + str(nueva_fecha_hora.second)
    return str_fecha_hora

def cleanup_old_logs(days_to_keep: int = 30, log_dir: str = "logs") -> dict:
    """
    Elimina archivos de log más antiguos que el número de días especificado
    
    Args:
        days_to_keep: Número de días de logs a mantener (default: 30)
        log_dir: Directorio de logs (default: "logs")
        
    Returns:
        dict: Estadísticas de limpieza (archivos eliminados, espacio liberado)
    """
    try:
        # Calcular fecha límite
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Buscar todos los archivos de log en el directorio
        log_patterns = [
            os.path.join(log_dir, "LOG_*.txt"),
            os.path.join(log_dir, "RPG_*.txt")
        ]
        
        deleted_files = []
        total_size_freed = 0
        
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    # Obtener fecha de modificación del archivo
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                    
                    # Si el archivo es más antiguo que la fecha límite, eliminarlo
                    if file_mtime < cutoff_date:
                        file_size = os.path.getsize(log_file)
                        os.remove(log_file)
                        deleted_files.append(os.path.basename(log_file))
                        total_size_freed += file_size
                        print(f"Log eliminado: {os.path.basename(log_file)} "
                              f"({file_size / 1024:.2f} KB, {file_mtime.strftime('%Y-%m-%d')})")
                
                except Exception as e:
                    print(f"Error eliminando {log_file}: {e}")
        
        # Convertir bytes a MB para mejor legibilidad
        size_mb = total_size_freed / (1024 * 1024) if total_size_freed > 0 else 0
        
        stats = {
            'deleted_count': len(deleted_files),
            'deleted_files': deleted_files,
            'size_freed_bytes': total_size_freed,
            'size_freed_mb': round(size_mb, 2),
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
            'days_kept': days_to_keep
        }
        
        if deleted_files:
            print(f"Limpieza completada: {len(deleted_files)} archivo(s) eliminado(s), "
                  f"{size_mb:.2f} MB liberados")
        else:
            print(f"No hay archivos de log anteriores a {cutoff_date.strftime('%Y-%m-%d')}")
        
        return stats
        
    except Exception as e:
        print(f"Error en limpieza de logs: {e}")
        return {
            'deleted_count': 0,
            'deleted_files': [],
            'size_freed_bytes': 0,
            'size_freed_mb': 0,
            'error': str(e)
        }

def send_telegram_notification(message: str) -> bool:
    """
    Envía un mensaje de notificación por Telegram usando la configuración de monitor_config.py
    
    Args:
        message: Mensaje a enviar
        
    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario
    """
    try:
        # Intentar importar la configuración de Telegram
        try:
            from monitor_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        except ImportError:
            print("[telegram] Configuración de Telegram no encontrada (monitor_config.py)")
            return False
        
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("[telegram] Credenciales de Telegram no configuradas")
            return False
        
        if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
            print("[telegram] Credenciales de Telegram no configuradas (placeholders)")
            return False
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        data = urllib.parse.urlencode(payload).encode()
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp_data = resp.read().decode()
                resp_json = json.loads(resp_data)
                if resp_json.get("ok"):
                    print("[telegram] Notificación enviada correctamente")
                    return True
                else:
                    print(f"[telegram] Error de API Telegram: {resp_json}")
                    return False
        except urllib.error.URLError as e:
            print(f"[telegram] Error de conexión: {e}")
            return False
        except Exception as e:
            print(f"[telegram] Error enviando mensaje: {e}")
            return False
            
    except Exception as e:
        print(f"[telegram] Error inesperado: {e}")
        return False

