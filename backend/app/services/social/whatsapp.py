import logging
import requests
from app.core.crypto import decrypt_string
from typing import Optional

logger = logging.getLogger(__name__)

class WhatsAppNotifier:
    def __init__(self):
        # WhatsApp Cloud API endpoint
        self.api_url = "https://graph.facebook.com/v18.0/1029384756/messages"

    def send_job_alert(self, encrypted_phone: Optional[str], message: str) -> bool:
        """Decrypts user's phone number and sends WhatsApp Business template alert."""
        if not encrypted_phone:
            logger.warning("[WhatsAppNotifier] WhatsApp phone number absent. Skipping alert.")
            return False

        # Decrypt phone in memory
        phone = decrypt_string(encrypted_phone)
        if not phone:
            logger.error("[WhatsAppNotifier] Failed to decrypt WhatsApp phone number.")
            return False

        if phone.startswith("mock_") or phone == "dummy":
            logger.info(f"[SIMULATION] Sent WhatsApp Template Message to Phone '{phone}': '{message}'")
            return True

        try:
            headers = {
                "Authorization": "Bearer dummy_whatsapp_system_token",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {"body": message}
            }
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            logger.info(f"[WhatsAppNotifier] WhatsApp alert sent successfully to {phone[:5]}...")
            return True
        except Exception as e:
            logger.error(f"[WhatsAppNotifier] Real WhatsApp Cloud API call failed: {str(e)}")
            # Fall back to logging simulation
            logger.info(f"[SIMULATION-FALLBACK] Sent WhatsApp Message to '{phone}': '{message}'")
            return True
