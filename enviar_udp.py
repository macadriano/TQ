import socket

ip_destino = "200.58.98.187"
puerto_destino = 6003

mensaje = ">RGP140426144108-4036.2540-07141.59460353171000001;&01;ID=95989;#0037*6A<"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    sock.sendto(mensaje.encode("ascii"), (ip_destino, puerto_destino))
    print("Mensaje UDP enviado correctamente")
finally:
    sock.close()