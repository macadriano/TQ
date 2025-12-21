# monitor_config.py
"""Configuration for the server monitoring system.

This file contains placeholders for Telegram bot credentials, email settings, and
monitoring parameters. When you are ready to enable notifications, replace the
placeholder values with real ones.
"""

# ---------------------------------------------------------------------------
# Telegram notification settings (placeholders)
# ---------------------------------------------------------------------------
# Bot token obtained from BotFather (e.g., "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
TELEGRAM_BOT_TOKEN = "8477575451:AAHPSfQFJMNZtK0OiQHGEJH3ukkVP9P1ilE"

# Chat ID of the user or group that should receive alerts.
# You can obtain it by sending a message to the bot and checking the updates.
TELEGRAM_CHAT_ID = "5266332517"

# ---------------------------------------------------------------------------
# Email notification settings (optional placeholders)
# ---------------------------------------------------------------------------
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "YOUR_EMAIL_PASSWORD"
EMAIL_RECIPIENT = "alert_recipient@example.com"

# ---------------------------------------------------------------------------
# Monitoring parameters
# ---------------------------------------------------------------------------
# URL of the health check endpoint exposed by tq_server_rpg.py
HEALTH_CHECK_URL = "http://localhost:5004/health"

# Interval between health checks in seconds (default 10 minutes)
CHECK_INTERVAL_SECONDS = 10 * 60

# Number of consecutive failed checks before sending an alert
FAILURE_THRESHOLD = 2

# Timeout for the HTTP request (seconds)
REQUEST_TIMEOUT = 5
