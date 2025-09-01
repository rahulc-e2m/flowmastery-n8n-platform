"""Security utilities for encryption and token generation"""

import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


class EncryptionManager:
    """Handles encryption and decryption of sensitive data with unique salts"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY.encode()
        self.iterations = 100000
    
    def _generate_key_from_salt(self, salt: bytes) -> bytes:
        """Generate encryption key from salt and secret key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.secret_key))
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string with unique salt per operation"""
        if not data:
            return ""
        
        # Generate unique salt for this encryption
        salt = secrets.token_bytes(16)  # 16 bytes = 128 bits
        
        # Generate key from salt
        key = self._generate_key_from_salt(salt)
        cipher_suite = Fernet(key)
        
        # Encrypt the data
        encrypted_data = cipher_suite.encrypt(data.encode())
        
        # Prepend salt to encrypted data (salt + encrypted_data)
        # Format: base64(salt) + ":" + base64(encrypted_data)
        salt_b64 = base64.urlsafe_b64encode(salt).decode()
        encrypted_b64 = base64.urlsafe_b64encode(encrypted_data).decode()
        
        return f"{salt_b64}:{encrypted_b64}"
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string, handling both old and new formats"""
        if not encrypted_data:
            return ""
        
        try:
            # Check if this is new format (contains salt)
            if ":" in encrypted_data:
                # New format: salt:encrypted_data
                salt_b64, encrypted_b64 = encrypted_data.split(":", 1)
                
                # Decode salt and encrypted data
                salt = base64.urlsafe_b64decode(salt_b64.encode())
                encrypted_bytes = base64.urlsafe_b64decode(encrypted_b64.encode())
                
                # Generate key from salt
                key = self._generate_key_from_salt(salt)
                cipher_suite = Fernet(key)
                
                # Decrypt
                return cipher_suite.decrypt(encrypted_bytes).decode()
            
            else:
                # Legacy format: try with old hardcoded salt for backward compatibility
                return self._decrypt_legacy(encrypted_data)
                
        except Exception as e:
            # If new format fails, try legacy format as fallback
            try:
                return self._decrypt_legacy(encrypted_data)
            except Exception:
                # If both fail, raise the original exception
                raise e
    
    def _decrypt_legacy(self, encrypted_data: str) -> str:
        """Decrypt data encrypted with the old hardcoded salt (backward compatibility)"""
        # Use old hardcoded salt for legacy data
        legacy_salt = b'flowmastery_salt'
        key = self._generate_key_from_salt(legacy_salt)
        cipher_suite = Fernet(key)
        
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def migrate_encrypted_field(self, old_encrypted_data: str) -> str:
        """Migrate old encrypted data to new format with unique salt"""
        if not old_encrypted_data:
            return ""
        
        # Decrypt with old format
        decrypted_data = self._decrypt_legacy(old_encrypted_data)
        
        # Re-encrypt with new format (unique salt)
        return self.encrypt(decrypted_data)


# Global encryption manager instance
encryption_manager = EncryptionManager()


def generate_invitation_token() -> str:
    """Generate a secure timestamped token for invitations"""
    import json
    import time
    
    # Create token payload with timestamp
    payload = {
        "random": secrets.token_urlsafe(24),  # Random component for uniqueness
        "timestamp": int(time.time()),        # Unix timestamp when token was created
        "type": "invitation"                  # Token type for validation
    }
    
    # Encrypt the payload
    payload_json = json.dumps(payload, separators=(',', ':'))  # Compact JSON
    encrypted_payload = encryption_manager.encrypt(payload_json)
    
    return encrypted_payload


def validate_invitation_token(token: str, max_age_hours: int = 48) -> dict:
    """
    Validate an invitation token and check if it's within the allowed age.
    
    Args:
        token: The encrypted invitation token
        max_age_hours: Maximum age of token in hours (default 48 hours)
    
    Returns:
        dict: Token payload if valid
        
    Raises:
        ValueError: If token is invalid, expired, or malformed
    """
    import json
    import time
    
    try:
        # Decrypt the token
        decrypted_payload = encryption_manager.decrypt(token)
        payload = json.loads(decrypted_payload)
        
        # Validate token structure
        required_fields = ["random", "timestamp", "type"]
        if not all(field in payload for field in required_fields):
            raise ValueError("Invalid token structure")
        
        # Validate token type
        if payload["type"] != "invitation":
            raise ValueError("Invalid token type")
        
        # Check token age
        current_time = int(time.time())
        token_age_seconds = current_time - payload["timestamp"]
        max_age_seconds = max_age_hours * 3600
        
        if token_age_seconds > max_age_seconds:
            raise ValueError(f"Token expired. Age: {token_age_seconds // 3600} hours, Max: {max_age_hours} hours")
        
        if token_age_seconds < 0:
            raise ValueError("Token timestamp is in the future")
        
        return payload
        
    except json.JSONDecodeError:
        raise ValueError("Invalid token format")
    except Exception as e:
        if "Token expired" in str(e) or "Token timestamp" in str(e):
            raise  # Re-raise our custom validation errors
        raise ValueError(f"Token validation failed: {str(e)}")


def is_invitation_token_expired(token: str, max_age_hours: int = 48) -> bool:
    """
    Check if an invitation token is expired without raising exceptions.
    
    Args:
        token: The encrypted invitation token
        max_age_hours: Maximum age of token in hours (default 48 hours)
    
    Returns:
        bool: True if token is expired or invalid, False if still valid
    """
    try:
        validate_invitation_token(token, max_age_hours)
        return False
    except ValueError:
        return True


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(48)