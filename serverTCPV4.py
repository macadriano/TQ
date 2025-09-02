import socket
import threading
import time
import protocolo
import funciones

#TerminalID=""

def handle_client(client_socket):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

             # Realizar cualquier operación necesaria con los datos recibidos
            print(data)
            valorHexa = funciones.bytes2hexa(data)
            print(valorHexa)
            funciones.guardarLog(valorHexa)   
            evento = protocolo.getPROTOCOL(valorHexa)
            if evento == "22":
                # convirtiendo a RGP de GEO5 si el TerminalID esta informado
                if len(TerminalID) > 0:
                    RGP = protocolo.RGPdesdeCHINO(valorHexa, TerminalID)   
                    # reenviando DATOS equipo chino convertido a GEO5 a plataforma GUS
                    funciones.enviar_mensaje_udp('179.43.115.190', 7007, RGP)
                    funciones.guardarLog(RGP)
                    #fechaHora = funciones.getFechaHora()
                    print("--> " + RGP)
            if evento == "01":
                # obteniendo ID de Terminal
                ##############################
                ## Extraer parámetros del mensaje
                # protocol_number, terminal_id, serial_number = protocolo.extract_parameters_from_message(data)
                ## Construir el paquete de respuesta
                # response_packet = protocolo.build_response_packet(protocol_number, terminal_id, serial_number)
                # client_socket.sendall(response_packet)
                TerminalID = protocolo.getIDok(valorHexa)
                funciones.guardarLog("TerminalID=" + TerminalID)                
            # ...
            # Responder al cliente si es necesario
            # client_socket.sendall(response)
    except socket.timeout:
        print("Se ha alcanzado el tiempo límite de inactividad.")
    finally:
        client_socket.close()
        TerminalID = ""

def start_server():
    host = '200.58.98.187'  # Cambiar por la dirección IP del servidor
    port = 5000  # Puerto del servidor

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"Servidor escuchando en {host}:{port}")
    #print(funciones.getFechaHora())
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexión establecida desde {addr[0]}:{addr[1]}")
        funciones.guardarLog(f"Cliente conectado: {addr[0]}:{addr[1]}")
        client_socket.settimeout(10)  # Establecer el tiempo de espera en segundos

        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

start_server()