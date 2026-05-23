import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)

def _get_fernet_key(key_str: str) -> bytes:
    """
    Safely derive a valid 32-byte base64-encoded Fernet key.
    If the key in settings is already valid, use it. Otherwise, derive it using SHA-256 and base64.
    """
    try:
        key_bytes = key_str.encode()
        # Verify it is a valid Fernet key format
        Fernet(key_bytes)
        return key_bytes
    except Exception:
        # Fallback: Hash key_str to 32 bytes and base64-encode it (urlsafe)
        hashed = hashlib.sha256(key_str.encode()).digest()
        derived_key = base64.urlsafe_b64encode(hashed)
        return derived_key

# Instantiate cipher based on the derived key
try:
    _fernet_key = _get_fernet_key(settings.ENCRYPTION_KEY)
    _cipher = Fernet(_fernet_key)
except Exception as e:
    logger.critical(f"Failed to initialize Fernet cipher: {str(e)}")
    raise e

def encrypt_string(plain_text: Optional[str]) -> Optional[str]:
    """Encrypt a plaintext string using AES-256 (returns base64-encoded ciphertext string)."""
    if plain_text is None:
        return None
    try:
        encrypted_bytes = _cipher.encrypt(plain_text.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Symmetric encryption failed: {str(e)}")
        return None

def decrypt_string(cipher_text: Optional[str]) -> Optional[str]:
    """Decrypt a base64-encoded ciphertext string using AES-256 (returns original plaintext string)."""
    if cipher_text is None:
        return None
    try:
        decrypted_bytes = _cipher.decrypt(cipher_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Symmetric decryption failed: {str(e)}")
        return None
