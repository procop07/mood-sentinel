import requests
import os
import logging

class NotificationService:
    """Handles sending notifications for alerts and reports."""

    def __init__(self, config: dict):
        """
        Initializes the NotificationService.
        Args:
            config: The application configuration dictionary.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Get Telegram settings from config and environment variables
        self.telegram_enabled = config.get('notifications', {}).get('telegram_enabled', True)
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if self.telegram_enabled:
            if not self.token or not self.chat_id:
                self.logger.warning("Telegram notifications enabled, but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set in .env file.")
                self.telegram_enabled = False
            else:
                self.logger.info("Telegram notifications enabled.")

    def _send_telegram(self, message: str):
        """Sends a message to Telegram."""
        if not self.telegram_enabled:
            self.logger.info("Telegram notifications are disabled, not sending message.")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            self.logger.info("Successfully sent message to Telegram.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send message to Telegram: {e}")

    def send_alerts(self, alerts: list, report: str):
        """
        Formats and sends a message for a list of alerts.
        Args:
            alerts: A list of alert dictionaries.
            report: A summary report string.
        """
        message = f"🚨 *Mood Sentinel Alert* 🚨\n\n"
        message += f"*Generated {len(alerts)} alerts.*\n\n"
        message += f"```{report}```"

        self._send_telegram(message)

    def send_report(self, report: str):
        """
        Formats and sends a periodic report.
        Args:
            report: The report content string.
        """
        message = f"📊 *Mood Sentinel Periodic Report* 📊\n\n"
        message += f"```{report}```"

        self._send_telegram(message)
