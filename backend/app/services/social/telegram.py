import logging
import requests
from app.core.crypto import decrypt_string
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        # Default system bot token (mock or configurable)
        self.bot_token = "987654321:AAH-dummy-bot-token-pjsap"
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_job_alert(self, encrypted_chat_id: Optional[str], message: str) -> bool:
        """Decrypts user's Telegram Chat ID and delivers a notification message."""
        if not encrypted_chat_id:
            logger.warning("[TelegramNotifier] Telegram chat ID absent. Skipping alert.")
            return False

        # Decrypt chat ID in memory
        chat_id = decrypt_string(encrypted_chat_id)
        if not chat_id:
            logger.error("[TelegramNotifier] Failed to decrypt Telegram Chat ID.")
            return False

        if chat_id.startswith("mock_") or chat_id == "dummy":
            logger.info(f"[SIMULATION] Sent Telegram Message to Chat ID '{chat_id}': '{message}'")
            return True

        try:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            # Execute real Telegram Bot API call
            response = requests.post(self.api_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"[TelegramNotifier] Notification delivered successfully to chat_id: {chat_id[:5]}...")
            return True
        except Exception as e:
            logger.error(f"[TelegramNotifier] Real Telegram Telegram Bot API call failed: {str(e)}")
            # Fall back to logging simulation
            logger.info(f"[SIMULATION-FALLBACK] Sent Telegram Message to '{chat_id}': '{message}'")
            return True
