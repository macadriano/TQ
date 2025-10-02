@echo off
echo ================================================================
echo SERVIDOR TQ SIMPLIFICADO
echo ================================================================
echo Solo procesa mensajes del formato RECORRIDO61674_011025.txt
echo ================================================================
echo.

python tq_server_simplificado.py --host 0.0.0.0 --port 5003 --udp-host 179.43.115.190 --udp-port 7007

pause
