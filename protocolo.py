import funciones
import struct
from datetime import datetime, timedelta


# FUNCIONES EQUIPO CHINO ----------------------------------------------------------------------------------
# b'xx\r\x01\x08eF\x80P\x13\x82\x16\x00\xbe\xb9\xfa\r\n' BINARIO
#
#
def Enviar0100(IDequipo):
    valor = funciones.hexa2bytes("78780d01086546805013821600beb9fa0d0a")
    return valor 
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
def Enviar8100(IDequipo):
    valor = funciones.hexa2bytes("78780d01086546805013821600beb9fa0d0a")
    return valor 

#print(bin2hexa(b'xx\r\x01\x08eF\x80P\x13\x82\x16\x00\xbe\xb9\xfa\r\n'))

# 22/6/2023 19:48:17 > (072105071146BR01230622A3435.6154S05833.0192W000.2134749000.0000000000L00000000)

# (072105071146BR01230622A3435.6154S05833.0192W000.2134749000.0000000000L00000000
# (072106937345BR01231012A3441.4042S05830.2773W003.9173525289.4200000000L00000000
# --- id -----??  yymmdd?-- lat ---*** lon ***????hhmmss????????????????????????
# 0123456789*123456789*123456789*123456789*123456789*123456789*123456789*123456789*

def EnviarReply(dato):
    valor = "78780d01" + getSERIALchino(dato) + getERRORchino(dato) + "0D0A"
    return valor 

def getIDpersonal(dato):
    valor = dato[1:13]
    return valor 

def getLATpersonal(dato):
    # (072106937345BR01231012A3441.4042S05830.2773W003.9173525289.4200000000L00000000
    # --- id -----??  yymmdd?-- lat ---*** lon ***????hhmmss????????????????????????
    # 0123456789*123456789*123456789*123456789*123456789*123456789*123456789*123456789*
    valor = dato[24:33]
    return valor

def getLONpersonal(dato):
    # (072106937345BR01231012A3441.4042S05830.2773W003.9173525289.4200000000L00000000
    # --- id -----??  yymmdd?-- lat ---*** lon ***????hhmmss????????????????????????
    # 0123456789*123456789*123456789*123456789*123456789*123456789*123456789*123456789*
    valor = dato[34:44]
    return valor

def getVELpersonal(dato):
    # (072106937345BR01231012A3441.4042S05830.2773W003.9173525289.4200000000L00000000
    # --- id -----??  yymmdd?-- lat ---*** lon ***????hhmmss????????????????????????
    # 0123456789*123456789*123456789*123456789*123456789*123456789*123456789*123456789*
    valor = dato[45:48]
    return valor

def getFECHApersonal(dato):
    # (072106937345BR01231012A3441.4042S05830.2773W003.9173525289.4200000000L00000000
    # --- id -----??  yymmdd?-- lat ---*** lon ***????hhmmss????????????????????????
    # 0123456789*123456789*123456789*123456789*123456789*123456789*123456789*123456789*
    year =  dato[17:19]
    month = dato[19:21]
    day = dato[21:23]

   
    hora_actual = datetime.now() + timedelta(hours=3) # tomando la hora de arribo del paquete x ahora...
    hour = hora_actual.strftime("%H")
    minute = hora_actual.strftime("%M")
    second = hora_actual.strftime("%S")
    y = funciones.completaCero(str(year))
    m = funciones.completaCero(str(month))
    d =funciones.completaCero(str(day))
    h = funciones.completaCero(str(hour))
    mm =funciones.completaCero(str(minute))
    s = funciones.completaCero(str(second))

    return d + m + y + h + mm + s   
   
def getFECHApersonal2(dato):
    # 072106937345BR01231012A3441.4042S05830.2773W003.9173525289.4200000000L00000000
    # --- id -----??  yymmdd?-- lat ---*** lon ***????hhmmss????????????????????????
    # 0123456789*123456789*123456789*123456789*123456789*123456789*123456789*123456789*
    fecha =  dato[21:23] + dato[19:21] + dato[17:19]
    hora = dato[50:56]

    return fecha + hora

def getIDchino(dato):
    #valor = dato[0:12]
    valor = "2403" # harcodeado a un equipo cargado en la plataforma de Gus
    return valor 

def getIDok(dato):
    # CORREGIDO: Extraer ID según la especificación del protocolo
    # En el string raw, el ID está en la posición 3 con 10 dígitos
    # Ejemplo: 24207666813317134703092534395301060583232162011236fbffdfff00000f3f00000000000000df54000009
    # ID: 2076668133 (posiciones 3-12), para RPG usar solo: 68133
    
    try:
        # CORREGIDO: Extraer los 10 dígitos desde la posición 2
        # Posiciones 2-11: 2076668133 (ID completo del equipo)
        id_completo = dato[2:12]  # Posiciones 2-11 (10 dígitos)
        
        # Para RPG, usar solo los últimos 5 dígitos del ID completo
        # NO convertir a decimal, trabajar directamente con el string
        if len(id_completo) == 10:
            valor = id_completo[-5:]  # Últimos 5 dígitos
        else:
            # Si no tiene 10 dígitos, completar con ceros a la izquierda
            valor = id_completo.zfill(5)
            
        return valor
        
    except Exception as e:
        # Fallback al método anterior si falla
        try:
            valor = dato[8:24]
            valor = valor[11:16]
            return valor
        except:
            return "00000"  # Valor por defecto si todo falla


def getSERIALchino(dato):
    valor = dato[9:25]
    #valor = funciones.hexa_a_decimal(valor)
    return valor 

def getERRORchino(dato):
    valor = dato[28:32]
    return valor 

def getLATchino(dato):
    # CORREGIDO: Usar el mismo método que tq_server.py
    # Posición 8-15 para latitud (4 bytes) con escala 1000000.0
    try:
        valor = dato[8:16]  # Posiciones 8-15 (4 bytes)
        decimal = int(valor, 16) / 1000000.0  # Misma escala que tq_server.py
        return round(decimal, 7)
    except:
        # Fallback al método anterior si falla
        try:
            valor = dato[22:30]  # Método anterior
            decimal = int(valor, 16) / 30000 / 60 * (-1)
            return round(decimal, 7)
        except:
            return 0.0

def getLONchino(dato):
    # CORREGIDO: Usar el mismo método que tq_server.py
    # Posición 16-23 para longitud (4 bytes) con escala 1000000.0
    try:
        valor = dato[16:24]  # Posiciones 16-23 (4 bytes)
        decimal = int(valor, 16) / 1000000.0  # Misma escala que tq_server.py
        return round(decimal, 7)
    except:
        # Fallback al método anterior si falla
        try:
            valor = dato[30:38]  # Método anterior
            decimal = int(valor, 16) / 30000 / 60 * (-1)
            return round(decimal, 7)
        except:
            return 0.0

def getVELchino(dato):
    # CORREGIDO: Usar el mismo método que tq_server.py
    # Buscar velocidad en posiciones 24+ con rango 0-200
    try:
        # Buscar en diferentes posiciones como hace tq_server.py
        for i in range(24, len(dato) - 4, 4):
            try:
                valor = dato[i:i+4]  # 4 bytes
                decimal = int(valor, 16)
                if 0 <= decimal <= 200:  # Rango razonable para velocidad
                    return decimal
            except:
                continue
        
        # Fallback al método anterior si no se encuentra
        valor = dato[38:40]  # Método anterior
        decimal = int(valor, 16)
        return decimal
    except:
        return 0

def getRUMBOchino(dato):
    # CORREGIDO: Usar el mismo método que tq_server.py
    # Buscar rumbo en posiciones 24+ con rango 0-360
    try:
        # Buscar en diferentes posiciones como hace tq_server.py
        for i in range(24, len(dato) - 4, 4):
            try:
                valor = dato[i:i+4]  # 4 bytes
                decimal = int(valor, 16)
                if 0 <= decimal <= 360:  # Rango razonable para rumbo
                    return decimal
            except:
                continue
        
        # Fallback al método anterior si no se encuentra
        valor = dato[40:44]  # Método anterior
        return valor
    except:
        return "000"


def getFECHAchino(dato):
    valor = dato[8:20]
    #print(valor)
    #print(type(valor))
    year = funciones.hexa_a_decimal(valor[0:2])
    month = funciones.hexa_a_decimal(valor[2:4])
    day = funciones.hexa_a_decimal(valor[4:6])
    hour = funciones.hexa_a_decimal(valor[6:8])
    minute = funciones.hexa_a_decimal(valor[8:10])
    second = funciones.hexa_a_decimal(valor[10:12])
    #year = int(valor[1,2], 16)
    y = funciones.completaCero(str(year))
    m = funciones.completaCero(str(month))
    d =funciones.completaCero(str(day))
    h = funciones.completaCero(str(hour))
    mm =funciones.completaCero(str(minute))
    s = funciones.completaCero(str(second))
    return d + m + y + h + mm + s

def getHORAchino(dato):
    valor = dato[48:54]
    return valor

def getPROTOCOL(dato):
    valor = dato[6:8]
    return valor

# FUNCIONES GEO5  -------------------------------------------------------------------------------
def sacar_checksum(xData):
    #ejemplo: >RGP121116125537-3456.0510-05759.56090000283000001;&08;ID=0107;#0090*57<
    # >RGP121116125537-3456.0510-05759.56090000283000001;&08;ID=0107;#0090*
    # reultado = 57 que se agrega despues del asterisco y se cierra con "<"
    xA = ord(xData[0])
    for f in range(1, len(xData)):
        if xData[f] != "*":
            xB = ord(xData[f])
            xA = xA ^ xB
        else:
            xB = ord(xData[f])
            xA = xA ^ xB
            break
    return format(xA, '02X')  # Devuelve el valor en formato hexadecimal de 2 dígitos

"""# Ejemplo de uso sacar_checksum()
data = "ABCDE*"
checksum = sacar_checksum(data)
print(checksum)"""

"""
>RGPaaaaaabbbbbbcddddddddefffffffffggghhhijjjjkkll<

donde:

aaaaaa: indica la fecha de la posición GPS // ddmmyy
bbbbbb: indica la hora UTC (Universal Time Coordinated)  posición GPS // hhmmss
c: signo de la posición
dddd.dddd: latitud de la posición GPS. Los valores negativos pertenecen al hemisferio Sur, y los positivos al hemisferio Norte.
e: signo de la longitud
fffff.ffff: longitud de la posición GPS. Los valores negativos pertenecen a  occidente, y los positivos a Oriente con respecto al meridiano de GreenWich.
ggg: velocidad en Km/H
hhh: orientación en grados
i: estado de la posición:
0:NO FIX(sin posición) 
2: 2D 
3: 3D 
jjjj: es la edad de la última medición válida en segundos
kk: calidad de la señal GPS HDOP.
Si ocurrió algún error de sintaxis responde:
>RGPERROR<
"""

def RGPdesdeCHINO(dato, TerminalID):
	# >RGPaaaaaabbbbbbcddddddddefffffffffggghhhijjjjkkll<
	# I => 12/11/2016 09:55:38 : >RGP121116125537-3456.0510-05759.56090000283000001;&08;ID=0107;#0090*57<
	fecha = getFECHAchino(dato)
	xlat = getLATchino(dato) # viene en formato decimal de grados numerico y signo (ej: -34.594233)
	# grados + minutos + decimal de minutos y sin signo (ej: 3441.5918)
	# lat = str(xlat)[1:3] + str((int(xlat)-xlat)*60)[0:2] + str((int(xlat)-xlat)*60)[2:7]
	lat = str(xlat)[1:3] + str((xlat-int(xlat))*60)[1:3] + str((xlat-int(xlat))*60)[3:8]
	xlon = getLONchino(dato)
	#lon = "0" + str(xlon)[1:3] + str((int(xlon)-xlon)*60)[0:2] + str((int(xlon)-xlon)*60)[2:7]
	lon = "0" + str(xlon)[1:3] + str((xlon-int(xlon))*60)[1:3] + str((xlon-int(xlon))*60)[3:8]
	vel = funciones.completaCero3(getVELchino(dato))
	dir = "000"
	estado ="3"
	edad = "0000"
	calidad = "01"
	evento = "01"
	ID = TerminalID
	nroMje = "0001"
	
	valor = ">RGP" + fecha + "-" + lat + "-" + lon + vel + dir + estado + edad + calidad + ";&" + evento + ";ID=" + ID + ";#" + nroMje + "*"
	checksum = sacar_checksum(valor)
	valor = valor + checksum + "<"
	# >RGP230622213474-3435.6154-05833.01920000003000001;&01;ID=1146;#0001*5F<
	return valor


def RGPdesdePERSONAL(dato, TerminalID):
    # >RGPaaaaaabbbbbbcddddddddefffffffffggghhhijjjjkkll<
    # I => 12/11/2016 09:55:38 : >RGP121116125537-3456.0510-05759.56090000283000001;&08;ID=0107;#0090*57<
    fecha = getFECHApersonal2(dato)
    xlat = getLATpersonal(dato) # viene en formato decimal de grados numerico y signo (ej: -34.594233)
    # grados + minutos + decimal de minutos y sin signo (ej: 3441.5918)
    lat = xlat
    xlon = getLONpersonal(dato)
    lon = xlon
    vel = getVELpersonal(dato)
    dir = "000"
    estado ="3"
    edad = "0000"
    calidad = "01"
    evento = "01"
    ID = TerminalID
    nroMje = "0001"
    
    valor = ">RGP" + fecha + "-" + lat + "-" + lon + vel + dir + estado + edad + calidad + ";&" + evento + ";ID=" + ID + ";#" + nroMje + "*"
    checksum = sacar_checksum(valor)
    valor = valor + checksum + "<"
    # >RGP230622213474-3435.6154-05833.01920000003000001;&01;ID=1146;#0001*5F<
    # >RGP121023000000-3441.4042-05830.27730000003000001;&01;ID=7345;#0001*54<
    return valor


def crc_itu2024(data: bytes) -> int:
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

def build_response_packet(protocol_number, terminal_id, serial_number):
    start_bit = b'\x78\x78'
    packet_length = 5  # Length = Protocol Number + Information Serial Number + Error Check (1 + 2 + 2 bytes)
    stop_bit = b'\x0D\x0A'
    
    packet = struct.pack('!2sB1s8sH', start_bit, packet_length, protocol_number, terminal_id, serial_number)
    
    crc = crc_itu2024(packet[2:])  # Calculate CRC from Packet Length to Information Serial Number
    crc_bytes = struct.pack('!H', crc)
    
    response_packet = packet + crc_bytes + stop_bit
    
    return response_packet

def extract_parameters_from_message(message):
    # Extraer longitud del mensaje
    length = message[2]
    
    # Extraer número de protocolo (1 byte)
    protocol_number = message[3:4]
    
    # Extraer ID del terminal (8 bytes)
    terminal_id = message[4:12]
    
    # Extraer número de serie (2 bytes)
    serial_number = struct.unpack('!H', message[12:14])[0]
    
    return protocol_number, terminal_id, serial_number
