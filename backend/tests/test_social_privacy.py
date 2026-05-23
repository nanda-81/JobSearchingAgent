import pytest
from fastapi import status
from app.core.crypto import encrypt_string, decrypt_string
from app.services.social import TwitterNotifier, TelegramNotifier, WhatsAppNotifier
from app.models.social import SocialCredentials
from app.models.audit import AuditLog
from app.models.user import User
from app.models.profile import UserProfile

# 1. Cryptographic AES-256 Symmetric Encryption tests
def test_symmetric_encryption_decryption():
    secret_payload = "my-super-secret-social-oauth-token-12345"
    
    # Encrypt
    cipher_text = encrypt_string(secret_payload)
    assert cipher_text is not None
    assert cipher_text != secret_payload
    
    # Decrypt
    plain_text = decrypt_string(cipher_text)
    assert plain_text == secret_payload

# 2. Social Notifiers Simulation tests
def test_social_notifiers_delivery():
    tw_notifier = TwitterNotifier()
    tg_notifier = TelegramNotifier()
    wa_notifier = WhatsAppNotifier()
    
    message = "New Python Job Matched! Relevancy: 95%"
    
    # Verify mock simulated paths return True (delivered)
    assert tw_notifier.send_job_alert(encrypt_string("mock_twitter_token"), message) is True
    assert tg_notifier.send_job_alert(encrypt_string("mock_chat_id"), message) is True
    assert wa_notifier.send_job_alert(encrypt_string("mock_phone_number"), message) is True

# 3. HTTP Auth Setup Helper
def _get_auth_token_for_user(client, email="privacy@example.com", name="Privacy User"):
    register_payload = {
        "email": email,
        "password": "mypassword123",
        "full_name": name
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_response = client.post("/api/v1/auth/token", data={
        "username": email,
        "password": "mypassword123"
    })
    return login_response.json()["access_token"]

# 4. Social Credentials Encryption API tests
def test_social_credentials_api_and_audit(client, db):
    token = _get_auth_token_for_user(client, "creds@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "twitter_token": "super_private_twitter_oauth_key",
        "telegram_chat_id": "telegram_chat_987",
        "whatsapp_phone": "+15551234567"
    }
    
    response = client.post("/api/v1/social/credentials", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Tokens and credentials securely encrypted and stored."
    
    # Assert database encrypted token
    user = db.query(User).filter(User.email == "creds@example.com").first()
    creds = db.query(SocialCredentials).filter(SocialCredentials.user_id == user.id).first()
    
    assert creds is not None
    assert creds.twitter_token != "super_private_twitter_oauth_key"
    assert decrypt_string(creds.twitter_token) == "super_private_twitter_oauth_key"
    
    # Assert Audit Log registered
    audit = db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.action == "update_social_credentials"
    ).first()
    assert audit is not None
    assert "twitter_token" in audit.payload["encrypted_fields"]

# 5. GDPR Compliance API tests
def test_gdpr_export_data_package(client, db):
    token = _get_auth_token_for_user(client, "gdpr-export@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Trigger export
    response = client.post("/api/v1/gdpr/export", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "user_profile" in data
    assert "targeting_preferences" in data
    assert "job_matches_history" in data
    assert "system_audit_logs" in data
    assert data["user_profile"]["email"] == "gdpr-export@example.com"
    
    # Check export audit log persisted
    user = db.query(User).filter(User.email == "gdpr-export@example.com").first()
    audit = db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.action == "gdpr_data_export"
    ).first()
    assert audit is not None

def test_gdpr_delete_forgotten_cascade(client, db):
    token = _get_auth_token_for_user(client, "gdpr-delete@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    user = db.query(User).filter(User.email == "gdpr-delete@example.com").first()
    user_id = user.id
    
    # Confirm user has profile initialized
    assert user.profile is not None
    
    # Trigger permanent deletion
    response = client.delete("/api/v1/gdpr/delete", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "permanently deleted" in response.json()["message"]
    
    # Verify User record is scrubbed
    deleted_user = db.query(User).filter(User.id == user_id).first()
    assert deleted_user is None
    
    # Verify UserProfile was cascadingly wiped
    deleted_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    assert deleted_profile is None
    
    # Verify compliance AuditLog persists, even though the user ID foreign key is set to NULL
    audit = db.query(AuditLog).filter(
        AuditLog.action == "gdpr_account_deletion"
    ).first()
    assert audit is not None
    assert audit.user_id is None  # FK was SET NULL cascadingly
    assert "deleted_email_hash" in audit.payload
