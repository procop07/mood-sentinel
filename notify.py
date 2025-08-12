import requests
import os
import logging
from typing import List, Dict, Any


def send_telegram(msg: str) -> bool:
    """Legacy function for sending telegram messages."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": msg})
        return response.status_code == 200
    except Exception:
        return False


class NotificationService:
    """Service for handling notifications across multiple channels."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the notification service with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get notification settings from config
        self.notifications_config = config.get('notifications', {})
        self.telegram_enabled = self.notifications_config.get('telegram_enabled', True)
        
        # Telegram configuration
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if self.telegram_enabled and (not self.telegram_token or not self.telegram_chat_id):
            self.logger.warning("Telegram notifications enabled but credentials not found")
            self.telegram_enabled = False
    
    def send_telegram_message(self, message: str) -> bool:
        """Send a message via Telegram."""
        if not self.telegram_enabled:
            self.logger.debug("Telegram notifications disabled")
            return False
            
        if not self.telegram_token or not self.telegram_chat_id:
            self.logger.error("Telegram credentials not configured")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def format_alerts(self, alerts: List[Dict[str, Any]]) -> str:
        """Format alerts into a readable message."""
        if not alerts:
            return "No alerts to report."
        
        message_lines = []
        message_lines.append("🚨 *MOOD SENTINEL ALERTS* 🚨")
        message_lines.append("")
        
        for i, alert in enumerate(alerts, 1):
            severity = alert.get('severity', 'Unknown').upper()
            alert_type = alert.get('type', 'Unknown')
            summary = alert.get('summary', 'No summary available')
            timestamp = alert.get('timestamp', 'Unknown time')
            
            # Use emoji based on severity
            severity_emoji = {
                'HIGH': '🔴',
                'MEDIUM': '🟡', 
                'LOW': '🟢',
                'CRITICAL': '💥'
            }.get(severity, '⚠️')
            
            message_lines.append(f"{severity_emoji} *Alert #{i}:*")
            message_lines.append(f"*Type:* {alert_type}")
            message_lines.append(f"*Severity:* {severity}")
            message_lines.append(f"*Summary:* {summary}")
            message_lines.append(f"*Time:* {timestamp[:19]}")
            
            # Add recommended actions if available
            actions = alert.get('actions', [])
            if actions:
                message_lines.append("*Recommended Actions:*")
                for action in actions[:3]:  # Limit to first 3 actions
                    message_lines.append(f"• {action}")
            
            message_lines.append("")  # Empty line between alerts
        
        message_lines.append(f"📊 *Total Alerts:* {len(alerts)}")
        
        return "\n".join(message_lines)
    
    def send_alerts(self, alerts: List[Dict[str, Any]], report: str = None) -> bool:
        """Send alert notifications."""
        if not alerts:
            self.logger.info("No alerts to send")
            return True
        
        try:
            # Format alerts for notification
            alert_message = self.format_alerts(alerts)
            
            # Add report summary if provided
            if report and report.strip():
                alert_message += "\n\n📋 *Report Summary:*\n" + report[:500]  # Limit report length
                if len(report) > 500:
                    alert_message += "\n... (truncated)"
            
            # Send via available channels
            success = True
            
            if self.telegram_enabled:
                telegram_success = self.send_telegram_message(alert_message)
                success = success and telegram_success
            
            if success:
                self.logger.info(f"Successfully sent {len(alerts)} alerts")
            else:
                self.logger.warning(f"Failed to send some or all alerts")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending alerts: {e}")
            return False
    
    def send_report(self, report: str) -> bool:
        """Send periodic report notifications."""
        if not report or not report.strip():
            self.logger.info("No report content to send")
            return True
        
        try:
            # Format report for notification
            report_message = f"📊 *MOOD SENTINEL REPORT*\n\n{report}"
            
            # Limit message length for Telegram
            if len(report_message) > 4000:
                report_message = report_message[:3950] + "\n\n... (report truncated)"
            
            # Send via available channels
            success = True
            
            if self.telegram_enabled:
                telegram_success = self.send_telegram_message(report_message)
                success = success and telegram_success
            
            if success:
                self.logger.info("Successfully sent periodic report")
            else:
                self.logger.warning("Failed to send periodic report")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending report: {e}")
            return False
    
    def test_connection(self) -> Dict[str, bool]:
        """Test notification service connections."""
        results = {}
        
        if self.telegram_enabled:
            test_message = "🧪 Mood Sentinel notification test"
            results['telegram'] = self.send_telegram_message(test_message)
        else:
            results['telegram'] = False
        
        return results
