"""Client configuration validation service"""

import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.services.client_service import ClientService
from app.services.n8n.client import N8nClient

logger = logging.getLogger(__name__)


class ClientConfigurationValidator:
    """Service to validate client n8n configuration comprehensively"""
    
    @staticmethod
    async def validate_client_n8n_config(
        db: AsyncSession, 
        client: Client
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Comprehensive validation of client n8n configuration
        
        Returns:
            Tuple of (is_valid, error_message, validation_details)
        """
        validation_details = {
            "has_api_url": bool(client.n8n_api_url),
            "has_encrypted_key": bool(client.n8n_api_key_encrypted),
            "api_key_decryption": "not_tested",
            "connection_test": "not_tested",
            "api_url": client.n8n_api_url,
            "client_id": client.id,
            "client_name": client.name
        }
        
        # Check basic configuration
        if not client.n8n_api_url:
            return False, "n8n API URL is not configured", validation_details
        
        if not client.n8n_api_key_encrypted:
            return False, "n8n API key is not configured", validation_details
        
        # Test API key decryption
        try:
            api_key = await ClientService.get_n8n_api_key(db, client.id)
            if not api_key:
                validation_details["api_key_decryption"] = "failed_null"
                return False, "n8n API key could not be decrypted (returned null)", validation_details
            
            if len(api_key.strip()) == 0:
                validation_details["api_key_decryption"] = "failed_empty"
                return False, "n8n API key decrypted to empty string", validation_details
            
            validation_details["api_key_decryption"] = "success"
            validation_details["api_key_length"] = len(api_key)
            
        except Exception as e:
            validation_details["api_key_decryption"] = f"failed_exception: {str(e)}"
            return False, f"n8n API key decryption failed: {str(e)}", validation_details
        
        # Test n8n connection
        try:
            connection_test = await ClientService.test_n8n_connection(
                client.n8n_api_url, api_key
            )
            
            validation_details["connection_test"] = connection_test.get("status", "unknown")
            validation_details["connection_healthy"] = connection_test.get("connection_healthy", False)
            validation_details["api_accessible"] = connection_test.get("api_accessible", False)
            validation_details["connection_message"] = connection_test.get("message", "")
            
            if not connection_test.get("connection_healthy", False):
                return False, f"n8n connection test failed: {connection_test.get('message', 'Unknown error')}", validation_details
            
        except Exception as e:
            validation_details["connection_test"] = f"failed_exception: {str(e)}"
            return False, f"n8n connection test failed: {str(e)}", validation_details
        
        return True, None, validation_details
    
    @staticmethod
    async def get_client_config_status(
        db: AsyncSession, 
        client: Client
    ) -> Dict[str, Any]:
        """
        Get detailed configuration status for a client
        """
        is_valid, error_message, details = await ClientConfigurationValidator.validate_client_n8n_config(
            db, client
        )
        
        return {
            "client_id": client.id,
            "client_name": client.name,
            "is_configured": is_valid,
            "error_message": error_message,
            "configuration_details": details,
            "has_n8n_api_key": is_valid,  # Only true if fully validated
            "n8n_api_url": client.n8n_api_url
        }
    
    @staticmethod
    def get_basic_config_status(client: Client) -> Dict[str, Any]:
        """
        Get basic configuration status without testing connections
        (for use in list endpoints where performance matters)
        """
        has_basic_config = bool(client.n8n_api_url and client.n8n_api_key_encrypted)
        
        return {
            "client_id": client.id,
            "client_name": client.name,
            "has_n8n_api_key": has_basic_config,
            "n8n_api_url": client.n8n_api_url,
            "has_api_url": bool(client.n8n_api_url),
            "has_encrypted_key": bool(client.n8n_api_key_encrypted)
        }


# Global instance
client_config_validator = ClientConfigurationValidator()