#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de Heartbeat UDP para TQ Server

Este módulo escucha heartbeats UDP del servidor principal (tq_server_rpg.py)
y envía alertas cuando el servidor está caído (no recibe heartbeats).

Puede ejecutarse en el mismo servidor o en un servidor remoto.
"""

import socket
import json
import time
import logging
import threading
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Importar configuración
try:
    import config
except ImportError:
    print("Error: No se pudo importar config.py")
    print("Asegúrate de que el archivo config.py existe en el directorio ControlTQ")
    sys.exit(1)


class HeartbeatMonitor:
    def __init__(self):
        """Inicializa el monitor de heartbeat"""
        self.udp_socket = None
        self.running = False
        self.last_heartbeat_time: Optional[datetime] = None
        self.last_heartbeat_data: Optional[dict] = None
        self.alert_sent = False
        self.last_alert_time: Optional[datetime] = None
        self.heartbeat_count = 0
        self.start_time: Optional[datetime] = None  # Tiempo de inicio del monitor
        
        # Configuración
        self.udp_host = config.UDP_LISTEN_HOST
        self.udp_port = config.UDP_LISTEN_PORT
        self.timeout_seconds = config.HEARTBEAT_TIMEOUT_SECONDS
        
        # Configurar logging
        self.setup_logging()
        
        # Logger
        self.logger = logging.getLogger('HeartbeatMonitor')
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(os.path.abspath(config.LOG_FILE)) if hasattr(config, 'LOG_FILE') else 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = config.LOG_FILE if hasattr(config, 'LOG_FILE') else 'logs/heartbeat_monitor.log'
        log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
        
        # Configurar logger
        logger = logging.getLogger('HeartbeatMonitor')
        logger.setLevel(log_level)
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    def send_telegram_alert(self, message: str) -> bool:
        """Envía una alerta por Telegram"""
        try:
            if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
                self.logger.warning("Credenciales de Telegram no configuradas")
                return False
            
            if config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
                self.logger.warning("Credenciales de Telegram no configuradas (placeholders)")
                return False
            
            import urllib.parse
            import urllib.request
            
            payload = {
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
            data = urllib.parse.urlencode(payload).encode()
            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp_data = resp.read().decode()
                resp_json = json.loads(resp_data)
                if resp_json.get("ok"):
                    self.logger.info("Alerta Telegram enviada correctamente")
                    return True
                else:
                    self.logger.error(f"Error API Telegram: {resp_json}")
                    return False
        except Exception as e:
            self.logger.error(f"Error enviando alerta Telegram: {e}")
            return False
    
    def send_email_alert(self, subject: str, body: str) -> bool:
        """Envía una alerta por Email"""
        if not config.EMAIL_ENABLED:
            return False
        
        try:
            if not config.SMTP_SERVER or not config.SMTP_USERNAME:
                self.logger.warning("Configuración SMTP no disponible")
                return False
            
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(body, 'plain', 'utf-8')
            msg["Subject"] = subject
            msg["From"] = config.SMTP_USERNAME
            msg["To"] = config.EMAIL_RECIPIENT
            
            with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                server.send_message(msg)
            
            self.logger.info("Alerta Email enviada correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error enviando alerta Email: {e}")
            return False
    
    def process_heartbeat(self, data: dict):
        """Procesa un heartbeat recibido"""
        current_time = datetime.now()
        
        # Si había una alerta previa y ahora recibimos heartbeat, es recuperación
        was_down = self.alert_sent
        
        # Actualizar tiempo del último heartbeat ANTES de verificar recuperación
        self.last_heartbeat_time = current_time
        self.last_heartbeat_data = data
        self.heartbeat_count += 1
        
        # Resetear flag de alerta solo después de actualizar last_heartbeat_time
        if was_down:
            self.alert_sent = False
            self.send_recovery_notification()
        else:
            # Si no estaba caído, asegurar que el flag esté reseteado
            self.alert_sent = False
        
        uptime = data.get('uptime_seconds', 0)
        server_id = data.get('server_id', 'tq_server_rpg')
        self.logger.info(f"Heartbeat recibido #{self.heartbeat_count} - Server: {server_id}, Uptime: {uptime}s")
    
    def send_recovery_notification(self):
        """Envía notificación de recuperación del servidor"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = (
            f"✅ *Servidor TQ Recuperado*\n"
            f"⏰ Hora: {timestamp}\n"
            f"🟢 El servidor ha vuelto a enviar heartbeats\n"
        )
        
        if self.last_heartbeat_data:
            uptime = self.last_heartbeat_data.get('uptime_seconds', 0)
            message += f"⏱️ Uptime: {uptime} segundos"
        
        self.send_telegram_alert(message)
        
        email_subject = "Servidor TQ Recuperado"
        email_body = f"El servidor TQ ha vuelto a funcionar correctamente.\n\nHora: {timestamp}"
        self.send_email_alert(email_subject, email_body)
    
    def check_timeout(self):
        """Verifica si ha pasado el timeout sin recibir heartbeat"""
        if not self.last_heartbeat_time:
            # Nunca recibimos un heartbeat
            # PERO esperar al menos un timeout completo desde el inicio antes de alertar
            if self.start_time:
                time_since_start = (datetime.now() - self.start_time).total_seconds()
                if time_since_start < self.timeout_seconds:
                    # Aún estamos en período de gracia inicial, no alertar
                    return
            
            # Solo alertar si ya pasó el timeout desde el inicio Y no se ha enviado alerta recientemente
            if not self.alert_sent or self.can_send_alert_again():
                self.send_down_alert("No se ha recibido ningún heartbeat desde el inicio")
                self.alert_sent = True
                self.last_alert_time = datetime.now()
            return
        
        elapsed = (datetime.now() - self.last_heartbeat_time).total_seconds()
        
        # IMPORTANTE: Solo alertar si realmente ha pasado el timeout completo
        # y si no se ha enviado una alerta recientemente (respetar cooldown)
        if elapsed > self.timeout_seconds:
            # Solo alertar si no se ha enviado alerta recientemente (cooldown)
            if not self.alert_sent or self.can_send_alert_again():
                self.logger.warning(f"Timeout detectado: {elapsed:.1f}s > {self.timeout_seconds}s")
                self.send_down_alert(f"Sin heartbeat por {elapsed:.0f} segundos")
                self.alert_sent = True
                self.last_alert_time = datetime.now()
        else:
            # Todo bien - estamos dentro del timeout, no alertar
            # Si había una alerta previa, solo resetear el flag cuando recibamos un heartbeat
            # NO resetear aquí porque podría causar problemas si el servidor está cerca del límite
            pass
    
    def can_send_alert_again(self) -> bool:
        """Verifica si puede enviar una nueva alerta (evitar spam)"""
        if not self.last_alert_time:
            return True
        
        cooldown = getattr(config, 'ALERT_COOLDOWN_SECONDS', 600)
        elapsed = (datetime.now() - self.last_alert_time).total_seconds()
        return elapsed >= cooldown
    
    def send_down_alert(self, reason: str):
        """Envía alerta de servidor caído"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        last_seen = ""
        if self.last_heartbeat_time:
            last_seen_delta = datetime.now() - self.last_heartbeat_time
            last_seen = f"Último heartbeat: {last_seen_delta.total_seconds():.0f} segundos atrás"
        
        message = (
            f"🚨 *Servidor TQ Caído*\n"
            f"⏰ Hora: {timestamp}\n"
            f"🔴 El servidor no está enviando heartbeats\n"
            f"❌ Razón: {reason}\n"
        )
        if last_seen:
            message += f"📅 {last_seen}"
        
        self.logger.error(f"Servidor caído detectado: {reason}")
        self.send_telegram_alert(message)
        
        email_subject = "ALERTA: Servidor TQ Caído"
        email_body = (
            f"El servidor TQ no está respondiendo.\n\n"
            f"Hora: {timestamp}\n"
            f"Razón: {reason}\n"
            f"{last_seen}\n"
        )
        self.send_email_alert(email_subject, email_body)
    
    def start(self):
        """Inicia el monitor"""
        try:
            # Crear socket UDP
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind((self.udp_host, self.udp_port))
            self.udp_socket.settimeout(1.0)  # Timeout para permitir verificación periódica
            
            self.running = True
            self.start_time = datetime.now()  # Registrar tiempo de inicio
            
            self.logger.info(f"Monitor de heartbeat iniciado en {self.udp_host}:{self.udp_port}")
            self.logger.info(f"Timeout configurado: {self.timeout_seconds} segundos")
            print(f"🚀 Monitor de Heartbeat iniciado en puerto {self.udp_port}")
            print(f"⏱️  Timeout: {self.timeout_seconds} segundos ({self.timeout_seconds/60:.1f} minutos)")
            print(f"📡 Esperando heartbeats del servidor TQ...")
            print(f"⏳ Período de gracia: {self.timeout_seconds} segundos antes de alertar")
            
            # Bucle principal
            while self.running:
                try:
                    # Intentar recibir heartbeat
                    data, addr = self.udp_socket.recvfrom(4096)
                    
                    try:
                        # Parsear JSON
                        heartbeat_data = json.loads(data.decode('utf-8'))
                        self.process_heartbeat(heartbeat_data)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Heartbeat con formato inválido desde {addr}: {e}")
                    except Exception as e:
                        self.logger.error(f"Error procesando heartbeat: {e}")
                
                except socket.timeout:
                    # Timeout esperado - verificar si el servidor está caído
                    self.check_timeout()
                    continue
                
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Error en socket UDP: {e}")
                    continue
                
        except Exception as e:
            self.logger.error(f"Error iniciando monitor: {e}")
            print(f"❌ Error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el monitor"""
        self.running = False
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
        self.logger.info("Monitor de heartbeat detenido")
        print("🛑 Monitor detenido")


def main():
    """Función principal"""
    import signal
    
    monitor = HeartbeatMonitor()
    
    def signal_handler(sig, frame):
        print("\n🛑 Deteniendo monitor...")
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n🛑 Interrupción detectada...")
    finally:
        monitor.stop()


if __name__ == "__main__":
    main()
