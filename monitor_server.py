# monitor_server.py
"""Monitoring script for TQ server.

This script periodically checks the health check endpoint exposed by
`tq_server_rpg.py`. If the server is down for a configurable number of
consecutive checks, it sends an alert via Telegram (or email). The
configuration is stored in `monitor_config.py`.

The script is designed to run as a background process (e.g. started
with `start_monitor.sh`).
"""

import time
import json
import sys
import threading
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Import configuration (placeholders for now)
try:
    from monitor_config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        SMTP_SERVER,
        SMTP_PORT,
        SMTP_USERNAME,
        SMTP_PASSWORD,
        EMAIL_RECIPIENT,
        HEALTH_CHECK_URL,
        CHECK_INTERVAL_SECONDS,
        FAILURE_THRESHOLD,
        REQUEST_TIMEOUT,
    )
except ImportError as e:
    print(f"[monitor] Error loading configuration: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def send_telegram_message(message: str) -> None:
    """Send a message via Telegram Bot API.

    If the placeholder values are not replaced, the request will fail –
    that's fine because the user will later provide real credentials.
    """
    import urllib.parse
    import urllib.request

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[monitor] Telegram credentials not configured – skipping notification")
        return

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }
    data = urllib.parse.urlencode(payload).encode()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        req = Request(url, data=data)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            resp_data = resp.read().decode()
            # Simple success check – Telegram returns JSON with "ok": true
            resp_json = json.loads(resp_data)
            if resp_json.get("ok"):
                print("[monitor] Telegram notification sent")
            else:
                print(f"[monitor] Telegram API error: {resp_json}")
    except Exception as exc:
        print(f"[monitor] Failed to send Telegram message: {exc}")


def send_email_alert(subject: str, body: str) -> None:
    """Send an email alert using SMTP.

    This function uses the placeholder SMTP configuration. If the user does
    not intend to use email, the function will simply log that email is not
    configured.
    """
    if not SMTP_SERVER or not SMTP_USERNAME:
        print("[monitor] SMTP configuration not set – skipping email alert")
        return
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USERNAME
        msg["To"] = EMAIL_RECIPIENT
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print("[monitor] Email alert sent")
    except Exception as exc:
        print(f"[monitor] Failed to send email: {exc}")


def check_health() -> bool:
    """Perform a single health‑check request.

    Returns True if the server reports status "ok"; otherwise False.
    """
    try:
        req = Request(HEALTH_CHECK_URL, headers={"User-Agent": "monitor/1.0"})
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                return False
            data = json.load(resp)
            return data.get("status") == "ok"
    except (URLError, HTTPError) as e:
        print(f"[monitor] Health check request failed: {e}")
        return False
    except Exception as exc:
        print(f"[monitor] Unexpected error during health check: {exc}")
        return False

# ---------------------------------------------------------------------------
# Main monitoring loop
# ---------------------------------------------------------------------------

def monitor_loop(stop_event: threading.Event) -> None:
    failure_count = 0
    while not stop_event.is_set():
        healthy = check_health()
        if healthy:
            if failure_count:
                print("[monitor] Server recovered – resetting failure counter")
            failure_count = 0
        else:
            failure_count += 1
            print(f"[monitor] Health check failed ({failure_count}/{FAILURE_THRESHOLD})")
            if failure_count >= FAILURE_THRESHOLD:
                # Build alert message
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"⚠️ *TQ Server Alert*\n"
                    f"Time: {timestamp}\n"
                    f"Reason: Health check endpoint not responding after {failure_count} attempts."
                )
                send_telegram_message(message)
                send_email_alert(
                    subject="TQ Server Down",
                    body=f"The TQ server health check failed at {timestamp}.",
                )
                # After alert, keep failure_count so we don't spam on every loop
                failure_count = 0
        # Wait for the next interval or stop event
        stop_event.wait(CHECK_INTERVAL_SECONDS)


def main() -> None:
    stop_event = threading.Event()
    try:
        print("[monitor] Starting monitoring loop…")
        monitor_loop(stop_event)
    except KeyboardInterrupt:
        print("[monitor] Received KeyboardInterrupt – stopping")
    finally:
        stop_event.set()

if __name__ == "__main__":
    main()
