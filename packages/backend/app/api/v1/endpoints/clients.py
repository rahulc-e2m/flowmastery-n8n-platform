"""Client management endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_admin_user, get_current_user, verify_client_access
from app.services.client_service import ClientService
from app.schemas.client import (
    ClientCreate,
    ClientUpdate, 
    ClientResponse,
    ClientN8nConfig
)

router = APIRouter()


@router.post("/", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Create a new client (admin only)"""
    client = await ClientService.create_client(db, client_data, admin_user)
    
    response = ClientResponse.model_validate(client)
    response.has_n8n_api_key = bool(client.n8n_api_key_encrypted)
    
    return response


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """List all clients (admin only)"""
    clients = await ClientService.get_all_clients(db)
    
    response_clients = []
    for client in clients:
        response = ClientResponse.model_validate(client)
        response.has_n8n_api_key = bool(client.n8n_api_key_encrypted)
        response_clients.append(response)
    
    return response_clients


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get client details"""
    # Verify client access
    if current_user.role != "admin" and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client"
        )
    client = await ClientService.get_client_by_id(db, client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    response = ClientResponse.model_validate(client)
    response.has_n8n_api_key = bool(client.n8n_api_key_encrypted)
    
    return response


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Update client details (admin only)"""
    client = await ClientService.update_client(db, client_id, client_data)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    response = ClientResponse.model_validate(client)
    response.has_n8n_api_key = bool(client.n8n_api_key_encrypted)
    
    return response


@router.post("/{client_id}/n8n-config")
async def configure_n8n_api(
    client_id: int,
    n8n_config: ClientN8nConfig,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Configure n8n API settings for a client (admin only)"""
    client = await ClientService.configure_n8n_api(db, client_id, n8n_config)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return {"message": "n8n API configuration updated successfully"}


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Delete a client (admin only)"""
    success = await ClientService.delete_client(db, client_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return {"message": "Client deleted successfully"}