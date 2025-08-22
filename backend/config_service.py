import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import hashlib
from cryptography.fernet import Fernet
import base64

class ConfigService:
    """Service to manage n8n API configuration with secure storage"""
    
    def __init__(self, config_dir: str = "data"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "n8n_config.json"
        self.key_file = self.config_dir / ".encryption_key"
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists or create one"""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Secure the key file permissions (Unix-like systems)
            try:
                os.chmod(self.key_file, 0o600)
            except:
                pass  # Windows or other systems
    
    def _get_encryption_key(self) -> bytes:
        """Get the encryption key"""
        with open(self.key_file, 'rb') as f:
            return f.read()
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value"""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted_bytes).decode()
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            return fernet.decrypt(encrypted_bytes).decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt value: {e}")
    
    def save_config(self, api_url: str, api_key: str, instance_name: str = "My n8n Instance") -> bool:
        """Save n8n configuration with encryption"""
        try:
            # Validate URL format
            if not api_url.startswith(('http://', 'https://')):
                raise ValueError("API URL must start with http:// or https://")
            
            # Clean the URL
            api_url = api_url.rstrip('/')
            if not api_url.endswith('/api/v1'):
                if api_url.endswith('/api'):
                    api_url += '/v1'
                elif not api_url.endswith('/v1'):
                    api_url += '/api/v1'
            
            # Encrypt sensitive data
            encrypted_api_key = self._encrypt_value(api_key)
            
            config = {
                "instance_name": instance_name,
                "api_url": api_url,  # URL is not encrypted as it's not sensitive
                "api_key": encrypted_api_key,  # Encrypted
                "created_at": str(Path().cwd()),  # Timestamp placeholder
                "last_updated": str(Path().cwd())  # Timestamp placeholder
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Secure the config file permissions
            try:
                os.chmod(self.config_file, 0o600)
            except:
                pass  # Windows or other systems
            
            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load n8n configuration with decryption"""
        try:
            if not self.config_file.exists():
                return None
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Decrypt sensitive data
            if 'api_key' in config:
                config['api_key'] = self._decrypt_value(config['api_key'])
            
            return config
        except Exception as e:
            print(f"Failed to load config: {e}")
            return None
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get configuration status without exposing sensitive data"""
        try:
            if not self.config_file.exists():
                return {
                    "configured": False,
                    "message": "No n8n configuration found"
                }
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Return status without sensitive data
            return {
                "configured": True,
                "instance_name": config.get('instance_name', 'Unknown'),
                "api_url": config.get('api_url', ''),
                "has_api_key": bool(config.get('api_key')),
                "last_updated": config.get('last_updated', 'Unknown')
            }
        except Exception as e:
            return {
                "configured": False,
                "error": str(e),
                "message": "Configuration file is corrupted or unreadable"
            }
    
    def delete_config(self) -> bool:
        """Delete the configuration file"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            return True
        except Exception as e:
            print(f"Failed to delete config: {e}")
            return False
    
    def validate_config(self, api_url: str, api_key: str) -> Dict[str, Any]:
        """Validate configuration parameters"""
        errors = []
        
        # Validate API URL
        if not api_url:
            errors.append("API URL is required")
        elif not api_url.startswith(('http://', 'https://')):
            errors.append("API URL must start with http:// or https://")
        elif len(api_url) < 10:
            errors.append("API URL seems too short")
        
        # Validate API Key
        if not api_key:
            errors.append("API Key is required")
        elif len(api_key) < 10:
            errors.append("API Key seems too short")
        elif ' ' in api_key:
            errors.append("API Key should not contain spaces")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def get_masked_api_key(self) -> str:
        """Get a masked version of the API key for display"""
        config = self.load_config()
        if not config or 'api_key' not in config:
            return ""
        
        api_key = config['api_key']
        if len(api_key) <= 8:
            return "*" * len(api_key)
        
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

# Global instance
config_service = ConfigService()
