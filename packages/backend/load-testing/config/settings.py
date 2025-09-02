"""Load testing configuration settings"""

import os
from typing import Dict, Any


class LoadTestSettings:
    """Load testing configuration"""
    
    # Base API settings
    BASE_URL = os.getenv("LOAD_TEST_BASE_URL", "http://localhost:8000")
    API_VERSION = os.getenv("API_VERSION", "v1")
    
    # Authentication settings
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "vivek.soni@e2m.solutions")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "13December200@@@")
    
    # Test user settings
    TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test.user@example.com")
    TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")
    
    # Load testing parameters
    DEFAULT_USERS = int(os.getenv("LOAD_TEST_USERS", "10"))
    DEFAULT_SPAWN_RATE = int(os.getenv("LOAD_TEST_SPAWN_RATE", "2"))
    DEFAULT_RUN_TIME = os.getenv("LOAD_TEST_RUN_TIME", "60s")
    
    # Request timeouts and limits
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Rate limiting
    MAX_REQUESTS_PER_SECOND = int(os.getenv("MAX_RPS", "100"))
    
    # Test data configuration
    GENERATE_TEST_DATA = os.getenv("GENERATE_TEST_DATA", "true").lower() == "true"
    TEST_CLIENT_COUNT = int(os.getenv("TEST_CLIENT_COUNT", "5"))
    TEST_USER_COUNT = int(os.getenv("TEST_USER_COUNT", "20"))
    
    # Database settings for test data cleanup
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/metrics_dashboard")
    
    # Reporting settings
    REPORTS_DIR = os.getenv("REPORTS_DIR", "./reports")
    ENABLE_CSV_EXPORT = os.getenv("ENABLE_CSV_EXPORT", "true").lower() == "true"
    ENABLE_HTML_REPORT = os.getenv("ENABLE_HTML_REPORT", "true").lower() == "true"
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS: Dict[str, Any] = {
        "auth_login_max_time": 1000,  # milliseconds
        "client_create_max_time": 2000,  # milliseconds
        "client_list_max_time": 500,  # milliseconds
        "metrics_query_max_time": 1500,  # milliseconds
        "health_check_max_time": 100,  # milliseconds
        "max_error_rate": 0.01,  # 1%
        "min_success_rate": 0.99  # 99%
    }
    
    @property
    def api_base_url(self) -> str:
        """Get the full API base URL"""
        return f"{self.BASE_URL}/api/{self.API_VERSION}"
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get default headers for authenticated requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


# Global settings instance
settings = LoadTestSettings()


# API endpoint mappings
API_ENDPOINTS = {
    # Authentication endpoints
    "auth_login": f"{settings.api_base_url}/auth/login",
    "auth_logout": f"{settings.api_base_url}/auth/logout",
    "auth_refresh": f"{settings.api_base_url}/auth/refresh",
    "auth_me": f"{settings.api_base_url}/auth/me",
    "auth_status": f"{settings.api_base_url}/auth/status",
    
    # Client management endpoints
    "clients_list": f"{settings.api_base_url}/clients/",
    "clients_create": f"{settings.api_base_url}/clients/",
    "clients_get": f"{settings.api_base_url}/clients/{{client_id}}",
    "clients_delete": f"{settings.api_base_url}/clients/{{client_id}}",
    "clients_n8n_config": f"{settings.api_base_url}/clients/{{client_id}}/n8n-config",
    "clients_test_n8n": f"{settings.api_base_url}/clients/test-n8n-connection",
    "clients_sync": f"{settings.api_base_url}/clients/{{client_id}}/sync-n8n",
    
    # Metrics endpoints
    "metrics_admin": f"{settings.api_base_url}/metrics/admin",
    "metrics_client": f"{settings.api_base_url}/metrics/client/{{client_id}}",
    "metrics_my": f"{settings.api_base_url}/metrics/my-metrics",
    "metrics_workflows": f"{settings.api_base_url}/metrics/client/{{client_id}}/workflows",
    "metrics_executions": f"{settings.api_base_url}/metrics/client/{{client_id}}/executions",
    "metrics_historical": f"{settings.api_base_url}/metrics/client/{{client_id}}/historical",
    
    # Health check endpoints
    "health_basic": f"{settings.BASE_URL}/health/",
    "health_detailed": f"{settings.BASE_URL}/health/detailed",
    
    # Cache endpoints
    "cache_clear_client": f"{settings.api_base_url}/cache/client/{{client_id}}",
    "cache_clear_all": f"{settings.api_base_url}/cache/all",
    
    # Task endpoints
    "tasks_sync_all": f"{settings.api_base_url}/tasks/sync-all",
    "tasks_aggregation": f"{settings.api_base_url}/tasks/aggregation/daily"
}


def get_endpoint_url(endpoint_name: str, **kwargs) -> str:
    """Get formatted endpoint URL with parameters"""
    url = API_ENDPOINTS.get(endpoint_name)
    if not url:
        raise ValueError(f"Unknown endpoint: {endpoint_name}")
    
    return url.format(**kwargs)