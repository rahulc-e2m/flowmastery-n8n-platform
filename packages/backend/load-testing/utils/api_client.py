"""API client wrapper for load testing"""

import json
import time
from typing import Dict, Any, Optional, Union
from config.settings import settings


class APIClient:
    """Enhanced API client wrapper for load testing"""
    
    def __init__(self, client):
        """Initialize with Locust HTTP client"""
        self.client = client
        self.base_url = settings.api_base_url
        self.default_timeout = settings.REQUEST_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
    
    def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retry_on_failure: bool = True,
        name: Optional[str] = None
    ) -> Optional[Any]:
        """Make HTTP request with error handling and retries"""
        
        # Prepare request parameters
        request_kwargs = {
            "url": endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint.lstrip('/')}",
            "timeout": timeout or self.default_timeout,
            "name": name or f"{method.lower()}_{endpoint.split('/')[-1]}"
        }
        
        if data:
            request_kwargs["json"] = data
        
        if params:
            request_kwargs["params"] = params
        
        if headers:
            request_kwargs["headers"] = headers
        else:
            request_kwargs["headers"] = {"Content-Type": "application/json"}
        
        # Perform request with retries
        for attempt in range(self.max_retries if retry_on_failure else 1):
            try:
                start_time = time.time()
                response = getattr(self.client, method.lower())(**request_kwargs)
                end_time = time.time()
                
                # Log performance metrics
                response_time_ms = (end_time - start_time) * 1000
                
                return {
                    "response": response,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "attempt": attempt + 1,
                    "success": 200 <= response.status_code < 300
                }
                
            except Exception as e:
                if attempt == self.max_retries - 1:  # Last attempt
                    return {
                        "response": None,
                        "status_code": None,
                        "error": str(e),
                        "attempt": attempt + 1,
                        "success": False
                    }
                
                # Wait before retry
                time.sleep(0.5 * (attempt + 1))
        
        return None
    
    def get(self, endpoint: str, **kwargs) -> Optional[Any]:
        """GET request wrapper"""
        return self.make_request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Any]:
        """POST request wrapper"""
        return self.make_request("POST", endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Any]:
        """PUT request wrapper"""
        return self.make_request("PUT", endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Optional[Any]:
        """DELETE request wrapper"""
        return self.make_request("DELETE", endpoint, **kwargs)
    
    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Any]:
        """PATCH request wrapper"""
        return self.make_request("PATCH", endpoint, data=data, **kwargs)


class ClientAPIClient:
    """Specialized API client for client management operations"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def create_client(self, client_data: Dict[str, Any], **kwargs) -> Optional[Any]:
        """Create a new client"""
        return self.api_client.post("/clients/", data=client_data, name="client_create", **kwargs)
    
    def list_clients(self, **kwargs) -> Optional[Any]:
        """List all clients"""
        return self.api_client.get("/clients/", name="client_list", **kwargs)
    
    def get_client(self, client_id: str, **kwargs) -> Optional[Any]:
        """Get client by ID"""
        return self.api_client.get(f"/clients/{client_id}", name="client_get", **kwargs)
    
    def update_client(self, client_id: str, update_data: Dict[str, Any], **kwargs) -> Optional[Any]:
        """Update client"""
        return self.api_client.put(f"/clients/{client_id}", data=update_data, name="client_update", **kwargs)
    
    def delete_client(self, client_id: str, **kwargs) -> Optional[Any]:
        """Delete client"""
        return self.api_client.delete(f"/clients/{client_id}", name="client_delete", **kwargs)
    
    def configure_n8n(self, client_id: str, n8n_config: Dict[str, Any], **kwargs) -> Optional[Any]:
        """Configure n8n API for client"""
        return self.api_client.post(
            f"/clients/{client_id}/n8n-config", 
            data=n8n_config, 
            name="client_n8n_config", 
            **kwargs
        )
    
    def test_n8n_connection(self, n8n_config: Dict[str, Any], **kwargs) -> Optional[Any]:
        """Test n8n connection"""
        return self.api_client.post(
            "/clients/test-n8n-connection", 
            data=n8n_config, 
            name="client_n8n_test", 
            **kwargs
        )
    
    def trigger_n8n_sync(self, client_id: str, **kwargs) -> Optional[Any]:
        """Trigger n8n data sync"""
        return self.api_client.post(f"/clients/{client_id}/sync-n8n", name="client_n8n_sync", **kwargs)


class MetricsAPIClient:
    """Specialized API client for metrics operations"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def get_admin_metrics(self, **kwargs) -> Optional[Any]:
        """Get admin-level metrics"""
        return self.api_client.get("/metrics/admin", name="metrics_admin", **kwargs)
    
    def get_client_metrics(self, client_id: str, **kwargs) -> Optional[Any]:
        """Get metrics for specific client"""
        return self.api_client.get(f"/metrics/client/{client_id}", name="metrics_client", **kwargs)
    
    def get_my_metrics(self, **kwargs) -> Optional[Any]:
        """Get metrics for current user's client"""
        return self.api_client.get("/metrics/my-metrics", name="metrics_my", **kwargs)
    
    def get_client_workflows(self, client_id: str, **kwargs) -> Optional[Any]:
        """Get workflow metrics for client"""
        return self.api_client.get(
            f"/metrics/client/{client_id}/workflows", 
            name="metrics_workflows", 
            **kwargs
        )
    
    def get_client_executions(
        self, 
        client_id: str, 
        limit: int = 50, 
        offset: int = 0, 
        **kwargs
    ) -> Optional[Any]:
        """Get execution data for client"""
        params = {"limit": limit, "offset": offset}
        return self.api_client.get(
            f"/metrics/client/{client_id}/executions", 
            params=params,
            name="metrics_executions", 
            **kwargs
        )
    
    def get_historical_metrics(
        self, 
        client_id: str, 
        period_type: str = "DAILY",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> Optional[Any]:
        """Get historical metrics for client"""
        params = {"period_type": period_type}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return self.api_client.get(
            f"/metrics/client/{client_id}/historical", 
            params=params,
            name="metrics_historical", 
            **kwargs
        )


class HealthAPIClient:
    """Specialized API client for health check operations"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def basic_health_check(self, **kwargs) -> Optional[Any]:
        """Basic health check"""
        return self.api_client.get("/health/", name="health_basic", **kwargs)
    
    def detailed_health_check(self, **kwargs) -> Optional[Any]:
        """Detailed health check with service status"""
        return self.api_client.get("/health/detailed", name="health_detailed", **kwargs)


class ResponseValidator:
    """Validate API responses for load testing"""
    
    @staticmethod
    def validate_success_response(result: Dict[str, Any], expected_fields: Optional[list] = None) -> bool:
        """Validate successful response"""
        if not result or not result.get("success"):
            return False
        
        response = result.get("response")
        if not response:
            return False
        
        if expected_fields:
            try:
                data = response.json()
                return all(field in data for field in expected_fields)
            except:
                return False
        
        return True
    
    @staticmethod
    def validate_client_response(result: Dict[str, Any]) -> bool:
        """Validate client-related response"""
        return ResponseValidator.validate_success_response(
            result, 
            expected_fields=["id", "name", "created_at"]
        )
    
    @staticmethod
    def validate_metrics_response(result: Dict[str, Any]) -> bool:
        """Validate metrics response"""
        return ResponseValidator.validate_success_response(result)
    
    @staticmethod
    def validate_auth_response(result: Dict[str, Any]) -> bool:
        """Validate authentication response"""
        return ResponseValidator.validate_success_response(
            result, 
            expected_fields=["user"]
        )


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor API performance during load tests"""
    
    def __init__(self):
        self.response_times = []
        self.error_count = 0
        self.success_count = 0
    
    def record_response(self, result: Dict[str, Any]):
        """Record API response metrics"""
        if result:
            response_time = result.get("response_time_ms", 0)
            self.response_times.append(response_time)
            
            if result.get("success"):
                self.success_count += 1
            else:
                self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.response_times:
            return {}
        
        total_requests = len(self.response_times)
        avg_response_time = sum(self.response_times) / total_requests
        min_response_time = min(self.response_times)
        max_response_time = max(self.response_times)
        
        # Calculate percentiles
        sorted_times = sorted(self.response_times)
        p50 = sorted_times[int(0.5 * len(sorted_times))]
        p95 = sorted_times[int(0.95 * len(sorted_times))]
        p99 = sorted_times[int(0.99 * len(sorted_times))]
        
        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / total_requests if total_requests > 0 else 0,
            "avg_response_time_ms": avg_response_time,
            "min_response_time_ms": min_response_time,
            "max_response_time_ms": max_response_time,
            "p50_response_time_ms": p50,
            "p95_response_time_ms": p95,
            "p99_response_time_ms": p99
        }
    
    def reset(self):
        """Reset performance metrics"""
        self.response_times.clear()
        self.error_count = 0
        self.success_count = 0