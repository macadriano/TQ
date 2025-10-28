@echo off
REM Script para iniciar el servidor TQ+RPG en segundo plano en Windows
REM Uso: start_server_rpg.bat

setlocal enabledelayedexpansion

REM Configuración
set SCRIPT_NAME=tq_server_rpg.py
set PID_FILE=%TEMP%\tq_server_rpg.pid
set LOG_FILE=tq_server_rpg.log
set PYTHON_CMD=python

echo 🚀 INICIANDO SERVIDOR TQ+RPG
echo ==================================

REM Verificar si el script existe
if not exist "%SCRIPT_NAME%" (
    echo ❌ Error: No se encuentra el archivo %SCRIPT_NAME%
    echo    Asegúrate de estar en el directorio correcto
    pause
    exit /b 1
)

REM Verificar si ya está ejecutándose
if exist "%PID_FILE%" (
    set /p EXISTING_PID=<"%PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | find "!EXISTING_PID!" >nul
    if !errorlevel! equ 0 (
        echo ⚠️  El servidor ya está ejecutándose (PID: !EXISTING_PID!)
        echo    Para detenerlo: stop_server_rpg.bat
        echo    Para ver estado: server_status_rpg.bat
        pause
        exit /b 1
    ) else (
        echo 🧹 Limpiando archivo PID obsoleto
        del "%PID_FILE%" 2>nul
    )
)

REM Verificar dependencias
echo 📋 Verificando dependencias...

REM Verificar Python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Error: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Verificar módulos Python necesarios
python -c "import socket, threading, logging, csv, os, math, requests, time, datetime" 2>nul
if !errorlevel! neq 0 (
    echo ❌ Error: Faltan módulos Python necesarios
    echo    Instala las dependencias: pip install requests
    pause
    exit /b 1
)

REM Verificar archivos de módulos
if not exist "funciones.py" (
    echo ❌ Error: No se encuentra funciones.py
    pause
    exit /b 1
)
if not exist "protocolo.py" (
    echo ❌ Error: No se encuentra protocolo.py
    pause
    exit /b 1
)

echo ✅ Dependencias verificadas

REM Crear directorio de logs si no existe
if not exist "logs" mkdir logs

REM Iniciar servidor en segundo plano
echo 🔄 Iniciando servidor en segundo plano...

REM Ejecutar con start para que se ejecute en segundo plano
start /b python "%SCRIPT_NAME%" --daemon > "%LOG_FILE%" 2>&1

REM Obtener PID del proceso iniciado (aproximado)
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find "python.exe"') do (
    set SERVER_PID=%%i
    set SERVER_PID=!SERVER_PID:"=!
    goto :found_pid
)
:found_pid

REM Guardar PID
echo !SERVER_PID! > "%PID_FILE%"

REM Esperar un momento para verificar que inició correctamente
timeout /t 2 /nobreak >nul

REM Verificar que el proceso sigue ejecutándose
tasklist /FI "PID eq !SERVER_PID!" 2>nul | find "!SERVER_PID!" >nul
if !errorlevel! equ 0 (
    echo ✅ Servidor iniciado correctamente
    echo    📊 PID: !SERVER_PID!
    echo    📁 Log: %LOG_FILE%
    echo    📁 PID File: %PID_FILE%
    echo.
    echo 🎯 COMANDOS DISPONIBLES:
    echo    Ver estado: server_status_rpg.bat
    echo    Detener: stop_server_rpg.bat
    echo    Ver logs: type %LOG_FILE%
    echo.
    echo 📡 Servidor escuchando en puerto 5003
    echo 📡 UDP configurado para reenvío a 179.43.115.190:7007
) else (
    echo ❌ Error: El servidor no pudo iniciarse
    echo    Revisa el log: type %LOG_FILE%
    del "%PID_FILE%" 2>nul
    pause
    exit /b 1
)

pause