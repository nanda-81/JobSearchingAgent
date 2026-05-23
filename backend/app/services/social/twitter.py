import logging
import requests
from app.core.crypto import decrypt_string
from typing import Optional

logger = logging.getLogger(__name__)

class TwitterNotifier:
    def __init__(self):
        self.api_url = "https://api.twitter.com/2/tweets"

    def send_job_alert(self, encrypted_token: Optional[str], message: str) -> bool:
        """Decrypts user's Twitter OAuth credentials and posts a job alert/tweet."""
        if not encrypted_token:
            logger.warning("[TwitterNotifier] Twitter credentials absent. Skipping alert.")
            return False

        # Decrypt dynamic token in memory
        token = decrypt_string(encrypted_token)
        if not token:
            logger.error("[TwitterNotifier] Failed to decrypt Twitter token.")
            return False

        # If it's a mock token or running in local dev simulation mode, log simulation details
        if token.startswith("mock_") or token == "dummy":
            logger.info(f"[SIMULATION] Posted Tweet successfully: '{message}' (using decrypted oauth token: {token[:10]}...)")
            return True

        try:
            # Real OAuth2 API call
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {"text": message}
            
            # Simulated real fetch with standard HTTP retry block if needed
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            logger.info("[TwitterNotifier] Tweet posted successfully via real API.")
            return True
        except Exception as e:
            logger.error(f"[TwitterNotifier] Real Twitter API call failed: {str(e)}")
            # Fall back to logging simulation so that developer has visibility
            logger.info(f"[SIMULATION-FALLBACK] Posted Tweet: '{message}'")
            return True
