"""n8n API client"""

import asyncio
import json
from typing import Dict, Any, Optional, List
import httpx
import logging
from datetime import datetime

from app.config import settings
from app.core.exceptions import N8nConnectionError, N8nAPIError

logger = logging.getLogger(__name__)


class N8nClient:
    """Async n8n API client"""
    
    def __init__(self):
        self.api_url = settings.N8N_API_URL
        self.api_key = settings.N8N_API_KEY
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "X-N8N-API-KEY": self.api_key or ""
                }
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def configure(self, api_url: str, api_key: str) -> bool:
        """Configure API credentials"""
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        
        # Reset client to use new credentials
        if self._client:
            asyncio.create_task(self._client.aclose())
            self._client = None
        
        return True
    
    async def health_check(self) -> bool:
        """Test n8n API connection"""
        if not self.api_url or not self.api_key:
            return False
        
        try:
            response = await self.request('GET', '/workflows', params={'limit': 1})
            return response is not None
        except Exception as e:
            logger.error(f"n8n health check failed: {e}")
            return False
    
    async def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make request to n8n API"""
        
        if not self.api_url or not self.api_key:
            raise N8nConnectionError("n8n API not configured")
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            logger.debug(f"n8n API request: {method} {url}")
            
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                error_msg = f"n8n API error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                
                raise N8nAPIError(error_msg, response.status_code)
                
        except httpx.RequestError as e:
            logger.error(f"n8n API request failed: {e}")
            raise N8nConnectionError(f"Failed to connect to n8n: {e}")
        except Exception as e:
            logger.error(f"n8n API unexpected error: {e}")
            raise N8nAPIError(f"Unexpected error: {e}")
    
    # Workflow methods
    async def get_workflows(self, active: Optional[bool] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get workflows"""
        params = {'limit': min(limit, 250)}
        if active is not None:
            params['active'] = str(active).lower()
        
        response = await self.request('GET', '/workflows', params=params)
        if response and isinstance(response, dict) and 'data' in response:
            return response['data']
        return response or []
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get single workflow"""
        response = await self.request('GET', f'/workflows/{workflow_id}')
        return response
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate workflow"""
        try:
            await self.request('POST', f'/workflows/{workflow_id}/activate')
            return True
        except Exception as e:
            logger.error(f"Failed to activate workflow {workflow_id}: {e}")
            return False
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate workflow"""
        try:
            await self.request('POST', f'/workflows/{workflow_id}/deactivate')
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate workflow {workflow_id}: {e}")
            return False
    
    # Execution methods
    async def get_executions(
        self, 
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get executions"""
        params = {'limit': min(limit, 250)}
        if workflow_id:
            params['workflowId'] = workflow_id
        if status:
            params['status'] = status
        
        response = await self.request('GET', '/executions', params=params)
        if response and isinstance(response, dict) and 'data' in response:
            return response['data']
        return response or []
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get single execution"""
        response = await self.request('GET', f'/executions/{execution_id}')
        return response
    
    # User methods
    async def get_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get users"""
        params = {'limit': min(limit, 250), 'includeRole': 'true'}
        response = await self.request('GET', '/users', params=params)
        if response and isinstance(response, dict) and 'data' in response:
            return response['data']
        return response or []
    
    # System methods
    async def get_variables(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get variables"""
        params = {'limit': min(limit, 250)}
        try:
            response = await self.request('GET', '/variables', params=params)
            if response and isinstance(response, dict) and 'data' in response:
                return response['data']
            return response or []
        except N8nAPIError as e:
            if "403" in str(e):
                # Variables endpoint may not be accessible
                logger.warning("Variables endpoint not accessible (403)")
                return []
            raise
    
    async def get_tags(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tags"""
        params = {'limit': min(limit, 250)}
        response = await self.request('GET', '/tags', params=params)
        if response and isinstance(response, dict) and 'data' in response:
            return response['data']
        return response or []


# Global client instance
n8n_client = N8nClient()