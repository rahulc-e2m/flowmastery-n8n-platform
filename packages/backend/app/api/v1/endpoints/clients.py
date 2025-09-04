"""Client management endpoints"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user, verify_client_access
from app.core.user_roles import UserRole, RolePermissions
from app.services.client_service import ClientService
from app.schemas.client import (
    ClientCreate,
    ClientUpdate, 
    ClientResponse,
    ClientN8nConfig,
    N8nConnectionTestResponse,
    ClientSyncResponse
)
from app.schemas.responses import (
    ClientCreatedResponse,
    ClientUpdatedResponse,
    ClientDeletedResponse,
    ClientListResponse
)
from app.core.decorators import validate_input, sanitize_response
from app.core.response_formatter import format_response

router = APIRouter()


@router.post("/", response_model=ClientCreatedResponse, status_code=status.HTTP_201_CREATED)
@validate_input(validate_emails=True, validate_urls=True, max_string_length=500)
@sanitize_response()
@format_response(
    message="Client created successfully",
    response_model=ClientCreatedResponse,
    status_code=201
)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Create a new client (admin only)"""
    client_service = ClientService()
    client = await client_service.create_client(db, client_data, admin_user)
    
    response = ClientResponse.model_validate(client)
    # Check both API URL and encrypted key for complete configuration
    response.has_n8n_api_key = bool(client.n8n_api_url and client.n8n_api_key_encrypted)
    
    return response


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """List all clients (admin only)"""
    client_service = ClientService()
    clients = await client_service.get_all_clients(db, use_cache=True)
    
    response_clients = []
    for client in clients:
        response = ClientResponse.model_validate(client)
        # Check both API URL and encrypted key for complete configuration
        response.has_n8n_api_key = bool(client.n8n_api_url and client.n8n_api_key_encrypted)
        response_clients.append(response)
    
    # Return the response in the format expected by ClientListResponse
    from app.schemas.api_standard import PaginatedResponse
    from datetime import datetime
    
    paginated_data: PaginatedResponse[ClientResponse] = PaginatedResponse[ClientResponse](
        items=response_clients,
        total=len(response_clients),
        page=1,
        size=len(response_clients),
        total_pages=1
    )
    
    return ClientListResponse(
        status="success",
        data=paginated_data,
        message="Clients retrieved successfully",
        timestamp=datetime.utcnow(),
        request_id=None
    )


@router.get("/{client_id}", response_model=ClientResponse)
@format_response(message="Client retrieved successfully")
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """Get client details"""
    # Verify client access
    if not RolePermissions.is_admin(current_user.role) and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client"
        )
    
    client_service = ClientService()
    client = await client_service.get_client_by_id(db, client_id, use_cache=True)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    response = ClientResponse.model_validate(client)
    # Check both API URL and encrypted key for complete configuration
    response.has_n8n_api_key = bool(client.n8n_api_url and client.n8n_api_key_encrypted)
    
    return response


@router.put("/{client_id}", response_model=ClientUpdatedResponse)
@validate_input(validate_emails=True, validate_urls=True, max_string_length=500)
@sanitize_response()
@format_response(
    message="Client updated successfully",
    response_model=ClientUpdatedResponse
)
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Update client details (admin only)"""
    client_service = ClientService()
    client = await client_service.update_client(db, client_id, client_data, admin_user)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    response = ClientResponse.model_validate(client)
    # Check both API URL and encrypted key for complete configuration
    response.has_n8n_api_key = bool(client.n8n_api_url and client.n8n_api_key_encrypted)
    
    return response


@router.post("/{client_id}/n8n-config", response_model=ClientSyncResponse)
@validate_input(validate_urls=True, max_string_length=1000)
@sanitize_response()
async def configure_n8n_api(
    client_id: str,
    n8n_config: ClientN8nConfig,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
) -> ClientSyncResponse:
    """Configure n8n API settings for a client and immediately sync data (admin only)"""
    client_service = ClientService()
    client = await client_service.configure_n8n_api(db, client_id, n8n_config, admin_user)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return ClientSyncResponse(
        message="n8n API configuration updated successfully",
        client_id=client.id,
        client_name=client.name,
        immediate_sync_triggered=True,
        note="Initial data sync completed. Additional data will continue syncing in the background."
    )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
@format_response(
    message="Client deleted successfully",
    status_code=204
)
async def delete_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
):
    """Delete a client (admin only)"""
    client_service = ClientService()
    success = await client_service.delete_client(db, client_id, admin_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return None


@router.post("/test-n8n-connection", response_model=N8nConnectionTestResponse)
@validate_input(validate_urls=True, max_string_length=1000)
@sanitize_response()
async def test_n8n_connection(
    n8n_config: ClientN8nConfig,
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
) -> N8nConnectionTestResponse:
    """Test n8n API connection without saving configuration (admin only)"""
    result = await ClientService.test_n8n_connection(
        n8n_config.n8n_api_url,
        n8n_config.n8n_api_key
    )
    
    return N8nConnectionTestResponse(**result)


@router.get("/{client_id}/config-status")
@format_response(message="Client configuration status retrieved successfully")
async def get_client_config_status(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
) -> Dict[str, Any]:
    """Get detailed configuration status for a client"""
    # Verify client access
    if not RolePermissions.is_admin(current_user.role) and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client"
        )
    
    client_service = ClientService()
    client = await client_service.get_client_by_id(db, client_id, use_cache=False)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    from app.services.client_config_validator import client_config_validator
    config_status = await client_config_validator.get_client_config_status(db, client)
    
    return config_status


@router.post("/{client_id}/sync-n8n")
@format_response(message="Immediate sync triggered successfully")
async def trigger_immediate_sync(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_user(required_roles=[UserRole.ADMIN]))
) -> Dict[str, Any]:
    """Manually trigger immediate n8n data sync for a client (admin only)"""
    client_service = ClientService()
    client = await client_service.get_client_by_id(db, client_id, use_cache=False)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    if not client.n8n_api_url or not client.n8n_api_key_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client n8n configuration not found. Please configure n8n API first."
        )
    
    # Test API key decryption and n8n connection
    try:
        api_key = await ClientService.get_n8n_api_key(db, client_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client n8n API key could not be decrypted. Please reconfigure n8n API."
            )
        
        # Test n8n connection to provide better error messages
        connection_test = await ClientService.test_n8n_connection(
            client.n8n_api_url, api_key
        )
        
        if not connection_test.get("connection_healthy", False):
            # Distinguish between configuration and service availability issues
            error_message = connection_test.get("message", "Unknown connection error")
            
            if "503" in error_message or "offline" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"n8n workspace is currently offline or unavailable: {error_message}. Please try again later or contact your n8n provider."
                )
            elif "401" in error_message or "403" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"n8n API authentication failed: {error_message}. Please reconfigure your n8n API key."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"n8n connection failed: {error_message}. Please check your n8n configuration."
                )
                
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Client n8n configuration validation failed: {str(e)}"
        )
    
    try:
        sync_result = await client_service._immediate_sync_n8n_data(db, client)
        return {
            "message": "Immediate sync completed successfully",
            "sync_result": sync_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
