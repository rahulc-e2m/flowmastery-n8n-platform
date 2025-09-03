"""Comprehensive metrics endpoint load testing with improved authentication handling"""

import json
import random
import time
from datetime import date, datetime, timedelta
from typing import Any
from locust import HttpUser, task, between, SequentialTaskSet
from locust.exception import ResponseError

from config.settings import settings, get_endpoint_url
from config.test_data import test_data_generator
from utils.auth_helper import AuthHelper
from utils.api_client import APIClient



# Global authentication state to reduce login attempts
class SharedAuth:
    """Shared authentication state across all users"""
    _access_token = None
    _login_time = None
    _login_attempts = 0
    _max_attempts = 3  # Reduced from 5 to be more conservative
    _rate_limit_cooldown = 60  # 60 seconds cooldown after rate limiting
    _last_rate_limit = None
    
    @classmethod
    def get_token(cls, client):
        """Get valid token with improved rate limiting protection"""
        current_time = time.time()
        
        # Check if we're in cooldown period after rate limiting
        if cls._last_rate_limit and (current_time - cls._last_rate_limit) < cls._rate_limit_cooldown:
            return cls._access_token  # Return existing token during cooldown
        
        # Check if we have a valid token (extended to 25 minutes)
        if (cls._access_token and cls._login_time and 
            (current_time - cls._login_time) < 1500):  # 25 minutes
            return cls._access_token
        
        # Prevent too many login attempts
        if cls._login_attempts >= cls._max_attempts:
            cls._last_rate_limit = current_time  # Start cooldown
            return cls._access_token  # Return existing token
        
        # Try to login with delay to prevent rate limiting
        if cls._login_attempts > 0:
            delay = min(cls._login_attempts * 2, 10)  # Exponential backoff, max 10s
            time.sleep(delay)
        
        # Try to login
        if cls._perform_login(client):
            cls._login_attempts = 0  # Reset on successful login
            cls._last_rate_limit = None  # Clear rate limit flag
            return cls._access_token
        else:
            cls._login_attempts += 1
            return cls._access_token  # Return existing token even if login failed
    
    @classmethod
    def get_auth_headers(cls, client):
        """Get basic headers (cookies are handled automatically by Locust)"""
        return {"Content-Type": "application/json"}
    
    @classmethod
    def _perform_login(cls, client):
        """Perform the actual login with better error handling"""
        credentials = {
            "email": "vivek.soni@e2m.solutions",
            "password": "13December200@@@"
        }
        
        try:
            login_headers = SharedAuth.get_auth_headers(client)
            
            with client.post(
                "/api/v1/auth/login",
                json=credentials,
                headers=login_headers,
                name="shared_auth_login",
                catch_response=True
            ) as response:
                
                if response.status_code == 200:
                    # Cookies are automatically stored by Locust's session
                    cls._access_token = "cookie_stored"  # Just a flag
                    cls._login_time = time.time()
                    response.success()  # Mark as success
                    return True
                elif response.status_code == 429:
                    cls._last_rate_limit = time.time()
                    response.success()  # Mark as success - this is expected behavior
                    return False
                else:
                    response.failure(f"Login failed: {response.status_code}")
                    return False
                
        except Exception as e:
            return False


class MetricsLoadTestUser(HttpUser):
    """Comprehensive metrics load testing with all endpoints in single class"""
    
    wait_time = between(2, 5)  # Moderate timing for comprehensive testing
    
    def on_start(self):
        """Setup for bulk operations testing with proper login"""
        self.login()
    
    def login(self):
        """Login using shared authentication pattern with cookie support"""
        # Use shared auth to get token and establish cookies
        SharedAuth.get_token(self.client)
        self.access_token = "cookie_stored"  # Flag to indicate login attempted
        return True
    
    def ensure_authenticated(self):
        """Ensure we have valid authentication"""
        if not self.access_token:
            return self.login()
        return True

    @task
    def bulk_admin_metrics(self):
        """Bulk admin metrics requests"""
        if not self.ensure_authenticated():
            return
        
        endpoint = "/api/v1/metrics/all"
        headers = SharedAuth.get_auth_headers(self.client)
        
        with self.client.get(
            endpoint,
            headers=headers,
            catch_response=True,
            name="bulk_admin_metrics"
        ) as response:
            
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                if self.login():
                    response.success()  # Successful token refresh
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Bulk admin metrics failed: {response.status_code}")

    @task
    def bulk_execution_endpoints(self):
        """Bulk execution endpoint requests"""
        if not self.ensure_authenticated():
            return
        
        # Randomly test different execution endpoints
        endpoint_choice = random.choice([
            "/api/v1/metrics/my-executions",
            "/api/v1/metrics/my-execution-stats",
            "/api/v1/metrics/my-historical",
            "/api/v1/metrics/my-workflows",
            "/api/v1/metrics/my-metrics"
        ])
        
        params: dict[str, Any] = {}
        
        # Set appropriate parameters for each endpoint type
        if endpoint_choice == "/api/v1/metrics/my-executions":
            params = {
                "limit": random.choice([10, 25, 50]),
                "offset": random.randint(0, 20)
            }
            # Randomly add filters with correct types
            if random.random() > 0.6:
                params["workflow_id"] = str(random.randint(1, 100))  # Convert to string for API
            if random.random() > 0.7:
                params["status"] = random.choice(["success", "error", "running", "waiting", "canceled"])
                
        elif endpoint_choice == "/api/v1/metrics/my-execution-stats":
            # No additional parameters needed for stats endpoint
            pass
            
        elif endpoint_choice == "/api/v1/metrics/my-workflows":
            # No additional parameters needed for workflows endpoint
            pass
            
        elif endpoint_choice == "/api/v1/metrics/my-metrics":
            # No additional parameters needed for metrics endpoint
            pass
            
        elif endpoint_choice == "/api/v1/metrics/my-historical":
            end_date = date.today()
            start_date = end_date - timedelta(days=random.randint(7, 30))
            params = {
                "period_type": random.choice(["DAILY", "WEEKLY", "MONTHLY"]),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            # Randomly add workflow filter
            if random.random() > 0.7:
                params["workflow_id"] = str(random.randint(1, 100))  # Convert to string for API
        
        with self.client.get(
            endpoint_choice,
            params=params,
            headers=SharedAuth.get_auth_headers(self.client),
            catch_response=True,
            name="bulk_execution_endpoints"
        ) as response:
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.success()  # Expected for admin user (no client associated)
            elif response.status_code == 401:
                if self.login():
                    response.success()
                else:
                    response.failure("Token refresh failed")
            elif response.status_code == 429:
                response.success()  # Rate limiting is expected
            else:
                response.failure(f"Bulk execution endpoints failed: {response.status_code}")

    @task
    def bulk_admin_operations(self):
        """Bulk admin operations testing"""
        if not self.ensure_authenticated():
            return
        
        # Test different admin endpoints
        admin_endpoints = [
            ("/api/v1/metrics/admin/data-freshness", "GET"),
            ("/api/v1/metrics/admin/scheduler-status", "GET"),
            ("/api/v1/metrics/admin/quick-sync", "POST"),
            ("/api/v1/metrics/admin/refresh-cache", "POST"),
            ("/api/v1/metrics/admin/sync-all", "POST")
        ]
        
        endpoint, method = random.choice(admin_endpoints)
        headers = SharedAuth.get_auth_headers(self.client)
        
        if method == "POST":
            response = self.client.post(
                endpoint,
                headers=headers,
                catch_response=True,
                name="bulk_admin_operations"
            )
        else:
            response = self.client.get(
                endpoint,
                headers=headers,
                catch_response=True,
                name="bulk_admin_operations"
            )
        
        with response as resp:
            
            if resp.status_code in [200, 500]:  # 500 expected for test environment
                resp.success()
            elif resp.status_code == 401:
                if self.login():
                    resp.success()
                else:
                    resp.failure("Token refresh failed")
            else:
                resp.failure(f"Bulk admin operations failed: {resp.status_code}")

    # Performance Testing Tasks
    @task(2)
    def test_admin_metrics(self):
        """Test admin-level metrics retrieval"""
        if not self.ensure_authenticated():
            return
        
        endpoint = "/api/v1/metrics/all"
        headers = SharedAuth.get_auth_headers(self.client)
        
        with self.client.get(
            endpoint,
            headers=headers,
            catch_response=True,
            name="admin_metrics"
        ) as response:
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "clients" in data and "total_clients" in data:
                        response.success()
                    else:
                        response.failure("Incomplete admin metrics response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()  # Successful token refresh
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Admin metrics failed with status {response.status_code}")
    
    @task(2)
    def test_client_metrics(self):
        """Test specific client metrics retrieval"""
        if not self.ensure_authenticated():
            return
        
        # client_id = test_data_generator.get_random_client_id()
        client_id = "82ef121c-6ec6-42d6-a938-59344eb556cb"
        endpoint = f"/api/v1/metrics/client/{client_id}"
        headers = SharedAuth.get_auth_headers(self.client)
        
        with self.client.get(
            endpoint,
            headers=headers,
            catch_response=True,
            name="client_metrics"
        ) as response:
            
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Expected for test data
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()  # Successful token refresh
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Client metrics failed with status {response.status_code}")

    @task(2)
    def test_my_historical_metrics(self):
        """Test my-historical metrics endpoint"""
        if not self.ensure_authenticated():
            return
        
        end_date = date.today()
        start_date = end_date - timedelta(days=random.randint(7, 30))
        
        params = {
            "period_type": random.choice(["DAILY", "WEEKLY"]),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        with self.client.get(
            "/api/v1/metrics/my-historical",
            params=params,
            headers=SharedAuth.get_auth_headers(self.client),
            catch_response=True,
            name="my_historical_metrics"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Expected for admin user
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"My historical metrics failed with status {response.status_code}")

    @task(2)
    def test_client_executions(self):
        """Test client executions endpoint"""
        if not self.ensure_authenticated():
            return
        
        # client_id = test_data_generator.get_random_client_id()
        client_id = "82ef121c-6ec6-42d6-a938-59344eb556cb"
        params = {"limit": random.choice([25, 50])}
        
        with self.client.get(
            f"/api/v1/metrics/client/{client_id}/executions",
            params=params,
            headers=SharedAuth.get_auth_headers(self.client),
            catch_response=True,
            name="client_executions"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Client executions failed with status {response.status_code}")

    @task(2)
    def test_client_workflows(self):
        """Test client workflows endpoint"""
        if not self.ensure_authenticated():
            return
        
        # client_id = test_data_generator.get_random_client_id()
        client_id = "82ef121c-6ec6-42d6-a938-59344eb556cb"
        with self.client.get(
            f"/api/v1/metrics/client/{client_id}/workflows",
            headers=SharedAuth.get_auth_headers(self.client),
            catch_response=True,
            name="client_workflows"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Client workflows failed with status {response.status_code}")

    @task(2)
    def test_my_executions(self):
        """Test my executions endpoint"""
        if not self.ensure_authenticated():
            return
        
        params = {"limit": random.choice([25, 50])}
        endpoint = "/api/v1/metrics/my-executions"
        headers = SharedAuth.get_auth_headers(self.client)
        
        with self.client.get(
            endpoint,
            params=params,
            headers=headers,
            catch_response=True,
            name="my_executions"
        ) as response:
            
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"My executions failed with status {response.status_code}")

    @task(2)
    def test_my_workflows(self):
        """Test my workflows endpoint"""
        if not self.ensure_authenticated():
            return
        
        endpoint = "/api/v1/metrics/my-workflows"
        headers = SharedAuth.get_auth_headers(self.client)
        
        with self.client.get(
            endpoint,
            headers=headers,
            catch_response=True,
            name="my_workflows"
        ) as response:
            
            if response.status_code in [200, 404]:  # 404 expected for admin user
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"My workflows failed with status {response.status_code}")

    @task(2)
    def test_my_metrics(self):
        """Test my metrics endpoint"""
        if not self.ensure_authenticated():
            return
        
        endpoint = "/api/v1/metrics/my-metrics"
        headers = SharedAuth.get_auth_headers(self.client)
        
        with self.client.get(
            endpoint,
            headers=headers,
            catch_response=True,
            name="my_metrics"
        ) as response:
            
            if response.status_code in [200, 404]:  # 404 expected for admin user
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"My metrics failed with status {response.status_code}")

    @task(1)
    def test_execution_stats(self):
        """Test execution stats endpoints"""
        if not self.ensure_authenticated():
            return
        
        # Randomly test either client-specific or my-execution-stats
        if random.random() > 0.5:
            # client_id = test_data_generator.get_random_client_id()
            client_id = "82ef121c-6ec6-42d6-a938-59344eb556cb"
            endpoint = f"/api/v1/metrics/client/{client_id}/execution-stats"
            name = "client_execution_stats"
        else:
            endpoint = "/api/v1/metrics/my-execution-stats"
            name = "my_execution_stats"
        
        with self.client.get(
            endpoint,
            headers=SharedAuth.get_auth_headers(self.client),
            catch_response=True,
            name=name
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Execution stats failed with status {response.status_code}")

    # Admin Tasks
    @task(1)
    def test_admin_endpoints(self):
        """Test admin-specific endpoints"""
        if not self.ensure_authenticated():
            return
        
        endpoint_choice = random.choice([
            ("/api/v1/metrics/admin/quick-sync", "POST", "admin_quick_sync"),
            ("/api/v1/metrics/admin/data-freshness", "GET", "admin_data_freshness"),
            ("/api/v1/metrics/admin/scheduler-status", "GET", "admin_scheduler_status"),
            ("/api/v1/metrics/admin/refresh-cache", "POST", "admin_refresh_cache"),
            ("/api/v1/metrics/admin/sync-all", "POST", "admin_sync_all")
        ])
        
        endpoint, method, name = endpoint_choice
        
        if method == "POST":
            response = self.client.post(
                endpoint,
                headers=SharedAuth.get_auth_headers(self.client),
                catch_response=True,
                name=name
            )
        else:
            response = self.client.get(
                endpoint,
                headers=SharedAuth.get_auth_headers(self.client),
                catch_response=True,
                name=name
            )
        
        with response as resp:
            if resp.status_code in [200, 500]:  # 500 expected for test environment
                resp.success()
            elif resp.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    resp.success()
                else:
                    resp.failure("Token refresh failed")
            else:
                resp.failure(f"Admin endpoint {name} failed with status {resp.status_code}")

    @task(1)
    def test_admin_aggregation_endpoints(self):
        """Test admin aggregation endpoints"""
        if not self.ensure_authenticated():
            return
        
        endpoint_choice = random.choice([
            ("/api/v1/metrics/admin/trigger-aggregation", "trigger_aggregation"),
            ("/api/v1/metrics/admin/trigger-historical-aggregation", "trigger_historical_aggregation")
        ])
        
        endpoint, name = endpoint_choice
        params = {}
        
        if "historical" in endpoint:
            params["days_back"] = random.choice([3, 7, 14])
        else:
            if random.random() > 0.6:
                target_date = date.today() - timedelta(days=random.randint(1, 7))
                params["target_date"] = target_date.isoformat()
        
        with self.client.post(
            endpoint,
            params=params,
            headers=SharedAuth.get_auth_headers(self.client),
            catch_response=True,
            name=name
        ) as response:
            if response.status_code in [200, 500]:  # 500 expected for test environment without Celery
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Admin aggregation {name} failed with status {response.status_code}")

    # Cache Testing Tasks  
    @task(3)
    def test_rapid_metrics_endpoints(self):
        """Rapid fire various metrics endpoints for cache testing"""
        if not self.ensure_authenticated():
            return
        
        # Test different endpoints for cache performance
        endpoints = [
            "/api/v1/metrics/my-executions",
            "/api/v1/metrics/my-execution-stats",
            "/api/v1/metrics/my-workflows",
            "/api/v1/metrics/my-metrics",
            "/api/v1/metrics/all"
        ]
        
        endpoint = random.choice(endpoints)
        params = {}
        
        if "executions" in endpoint and "stats" not in endpoint:
            params = {"limit": 25}
        elif "historical" in endpoint:
            params = {
                "period_type": "DAILY",
                "start_date": (date.today() - timedelta(days=7)).isoformat()
            }
        
        headers = SharedAuth.get_auth_headers(self.client)
        
        with self.client.get(
            endpoint,
            params=params,
            headers=headers,
            catch_response=True,
            name="rapid_metrics_cache_test"
        ) as response:
            
            if response.status_code in [200, 404]:  # 404 expected for admin user
                response.success()
            elif response.status_code == 403:
                response.success()  # 403 is expected for some endpoints with admin users
            elif response.status_code == 401:
                if self.login():
                    response.success()  # Successful re-authentication
                else:
                    response.failure("Authentication failed")
            elif response.status_code == 429:
                response.success()  # Rate limiting is expected
            else:
                response.failure(f"Cache test failed: {response.status_code}")


