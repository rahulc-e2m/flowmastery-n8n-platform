"""Security utilities for encryption and token generation"""

import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""
    
    def __init__(self):
        # Generate key from SECRET_KEY
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'flowmastery_salt',  # In production, use a random salt per client
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        self.cipher_suite = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        if not data:
            return ""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        if not encrypted_data:
            return ""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()


# Global encryption manager instance
encryption_manager = EncryptionManager()


def generate_invitation_token() -> str:
    """Generate a secure random token for invitations"""
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(48)