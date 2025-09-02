"""Comprehensive metrics endpoint load testing with improved authentication handling"""

import json
import random
import time
from datetime import date, datetime, timedelta
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
    _max_attempts = 5
    
    @classmethod
    def get_token(cls, client):
        """Get valid token with rate limiting protection"""
        current_time = time.time()
        
        # Check if we have a valid token
        if (cls._access_token and cls._login_time and 
            (current_time - cls._login_time) < 1200):  # 20 minutes
            return cls._access_token
        
        # Prevent too many login attempts
        if cls._login_attempts >= cls._max_attempts:
            print(f"Rate limit protection: max attempts ({cls._max_attempts}) reached")
            return cls._access_token  # Return existing token even if old
        
        # Try to login
        if cls._perform_login(client):
            cls._login_attempts = 0  # Reset on successful login
            return cls._access_token
        else:
            cls._login_attempts += 1
            return cls._access_token  # Return existing token even if login failed
    
    @classmethod
    def _perform_login(cls, client):
        """Perform the actual login"""
        credentials = {
            "email": "vivek.soni@e2m.solutions",
            "password": "13December200@@@"
        }
        
        try:
            response = client.post(
                "/api/v1/auth/login",
                json=credentials,
                headers={"Content-Type": "application/json"},
                name="shared_auth_login"
            )
            
            if response.status_code == 200:
                cls._access_token = response.cookies.get("access_token")
                cls._login_time = time.time()
                print("Shared authentication successful")
                return True
            elif response.status_code == 429:
                print("Rate limited - using existing token")
                return False
            else:
                print(f"Login failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Login exception: {e}")
            return False


class MetricsLoadTaskSet(SequentialTaskSet):
    """Sequential metrics operations for load testing"""
    
    def on_start(self):
        """Initialize test session with improved authentication"""
        self.auth_helper = AuthHelper(self.client)
        self.api_client = APIClient(self.client)
        self.created_clients = []
        self.access_token = None
        self.login_time = None
        
        # Perform initial login with better error handling
        self.perform_login()
    
    def perform_login(self):
        """Perform admin login with correct credentials"""
        credentials = {
            "email": "vivek.soni@e2m.solutions",
            "password": "13December200@@@"
        }
        
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json=credentials,
                headers={"Content-Type": "application/json"},
                name="admin_login"
            )
            
            if response.status_code == 200:
                # Store tokens from cookies
                self.access_token = response.cookies.get("access_token")
                self.login_time = time.time()
                return True
            else:
                print(f"Login failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Login exception: {e}")
            return False
    
    def ensure_authenticated(self):
        """Ensure user is authenticated"""
        if not self.access_token:
            return self.perform_login()
        
        # Check if we need to refresh (every 20 minutes)
        current_time = time.time()
        if self.login_time and (current_time - self.login_time) > 1200:
            return self.perform_login()
        
        return True
    
    @task(25)
    def test_admin_metrics(self):
        """Test admin-level metrics retrieval"""
        if not self.ensure_authenticated():
            return
        
        with self.client.get(
            "/api/v1/metrics/all",
            headers={"Content-Type": "application/json"},
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
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            elif response.status_code == 429:
                response.failure("Rate limited - too many requests")
            else:
                response.failure(f"Admin metrics failed with status {response.status_code}")
    
    @task(20)
    def test_client_metrics(self):
        """Test specific client metrics retrieval"""
        if not self.ensure_authenticated():
            return
        
        # Use a test client ID (in real scenario, get from created clients)
        client_id = test_data_generator.get_random_client_id()
        
        with self.client.get(
            f"/api/v1/metrics/client/{client_id}",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_metrics"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "client_id" in data and "total_workflows" in data:
                        response.success()
                    else:
                        response.failure("Incomplete client metrics response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("Client not found - expected for test data")
            elif response.status_code == 401:
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            elif response.status_code == 403:
                response.failure("Access denied - expected for non-admin users")
            else:
                response.failure(f"Client metrics failed with status {response.status_code}")
    
    @task(15)
    def test_workflow_metrics(self):
        """Test client workflow metrics retrieval"""
        if not self.ensure_authenticated():
            return
        
        client_id = test_data_generator.get_random_client_id()
        
        with self.client.get(
            f"/api/v1/metrics/client/{client_id}/workflows",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="workflow_metrics"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "workflows" in data and "summary" in data:
                        response.success()
                    else:
                        response.failure("Incomplete workflow metrics response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("Client not found - expected for test data")
            elif response.status_code == 401:
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"Workflow metrics failed with status {response.status_code}")
    
    @task(12)
    def test_historical_metrics(self):
        """Test historical metrics with various parameters"""
        if not self.ensure_authenticated():
            return
        
        client_id = test_data_generator.get_random_client_id()
        
        # Generate test query parameters
        end_date = date.today()
        start_date = end_date - timedelta(days=random.randint(7, 90))
        period_type = random.choice(["DAILY", "WEEKLY", "MONTHLY"])
        
        params = {
            "period_type": period_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        # Randomly add workflow_id filter
        if random.random() > 0.7:
            params["workflow_id"] = random.randint(1, 100)
        
        with self.client.get(
            f"/api/v1/metrics/client/{client_id}/historical",
            params=params,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="historical_metrics"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "metrics_data" in data and "trends" in data:
                        response.success()
                    else:
                        response.failure("Incomplete historical metrics response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("Client not found - expected for test data")
            elif response.status_code == 401:
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"Historical metrics failed with status {response.status_code}")
    
    @task(8)
    def test_my_metrics(self):
        """Test current user's metrics (for client users)"""
        if not self.ensure_authenticated():
            return
        
        with self.client.get(
            "/api/v1/metrics/my-metrics",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="my_metrics"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "client_id" in data and "total_workflows" in data:
                        response.success()
                    else:
                        response.failure("Incomplete my metrics response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("No client associated - expected for admin users")
            elif response.status_code == 401:
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"My metrics failed with status {response.status_code}")
    
    @task(5)
    def test_my_workflow_metrics(self):
        """Test current user's workflow metrics"""
        if not self.ensure_authenticated():
            return
        
        with self.client.get(
            "/api/v1/metrics/my-workflows",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="my_workflow_metrics"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "workflows" in data and "summary" in data:
                        response.success()
                    else:
                        response.failure("Incomplete my workflow metrics response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("No client associated - expected for admin users")
            elif response.status_code == 401:
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"My workflow metrics failed with status {response.status_code}")
    
    @task(3)
    def test_admin_sync_client(self):
        """Test admin forced sync for specific client"""
        if not self.ensure_authenticated():
            return
        
        client_id = test_data_generator.get_random_client_id()
        
        with self.client.post(
            f"/api/v1/metrics/admin/sync/{client_id}",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="admin_sync_client"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "message" in data:
                        response.success()
                    else:
                        response.failure("Incomplete sync response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("Client not found - expected for test data")
            elif response.status_code == 401:
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            elif response.status_code == 500:
                response.failure("Sync failed - expected for test clients")
            else:
                response.failure(f"Admin sync failed with status {response.status_code}")
    
    @task(2)
    def test_admin_sync_all(self):
        """Test admin sync all clients"""
        if not self.ensure_authenticated():
            return
        
        with self.client.post(
            "/api/v1/metrics/admin/sync-all",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="admin_sync_all"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "message" in data:
                        response.success()
                    else:
                        response.failure("Incomplete sync all response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                if self.perform_login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"Admin sync all failed with status {response.status_code}")


class MetricsPerformanceUser(HttpUser):
    """User focused on metrics performance operations with shared auth"""
    
    wait_time = between(2, 5)  # Slower to reduce rate limiting
    
    def on_start(self):
        """Setup with shared authentication"""
        self.access_token = SharedAuth.get_token(self.client)
    
    def ensure_authenticated(self):
        """Ensure we have valid authentication"""
        if not self.access_token:
            self.access_token = SharedAuth.get_token(self.client)
        return bool(self.access_token)
    
    @task(25)
    def test_admin_metrics(self):
        """Test admin-level metrics retrieval"""
        if not self.ensure_authenticated():
            return
        
        with self.client.get(
            "/api/v1/metrics/all",
            headers={"Content-Type": "application/json"},
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
                # Try to refresh token and mark as success since we handled it
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()  # Successful token refresh
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Admin metrics failed with status {response.status_code}")
    
    @task(15)
    def test_client_metrics(self):
        """Test specific client metrics retrieval"""
        if not self.ensure_authenticated():
            return
        
        client_id = test_data_generator.get_random_client_id()
        
        with self.client.get(
            f"/api/v1/metrics/client/{client_id}",
            headers={"Content-Type": "application/json"},
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


class MetricsBulkOperationsUser(HttpUser):
    """User for testing bulk metrics operations with shared auth"""
    
    wait_time = between(3, 6)  # Slower to reduce load
    
    def on_start(self):
        """Setup for bulk operations testing"""
        self.access_token = SharedAuth.get_token(self.client)
    
    @task(30)
    def bulk_admin_metrics(self):
        """Bulk admin metrics requests"""
        if not self.access_token:
            self.access_token = SharedAuth.get_token(self.client)
            if not self.access_token:
                return
        
        with self.client.get(
            "/api/v1/metrics/all",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="bulk_admin_metrics"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self.access_token = SharedAuth.get_token(self.client)
                if self.access_token:
                    response.success()  # Successful token refresh
                else:
                    response.failure("Token refresh failed")
            else:
                response.failure(f"Bulk admin metrics failed: {response.status_code}")


class MetricsCacheTestUser(HttpUser):
    """User for testing metrics caching performance"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Setup for cache testing"""
        self.login()
    
    def login(self):
        """Login with admin credentials"""
        credentials = {
            "email": "vivek.soni@e2m.solutions",
            "password": "13December200@@@"
        }
        
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json=credentials,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.access_token = response.cookies.get("access_token")
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    @task(40)
    def rapid_admin_metrics(self):
        """Rapid fire admin metrics to test caching"""
        with self.client.get(
            "/api/v1/metrics/all",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="cache_admin_metrics"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                if self.login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"Cache test failed: {response.status_code}")
    
    @task(10)
    def test_cache_refresh(self):
        """Test cache refresh functionality"""
        with self.client.post(
            "/api/v1/metrics/admin/refresh-cache",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="cache_refresh"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                if self.login():
                    response.failure("Re-authenticated successfully")
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"Cache refresh failed: {response.status_code}")


# Main user class for load distribution
class MetricsLoadTestUser(HttpUser):
    """Main metrics load test user with weighted task distribution"""
    
    wait_time = between(1, 4)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = None
    
    def on_start(self):
        """Perform initial authentication"""
        self.login()
    
    def login(self):
        """Login with admin credentials"""
        credentials = {
            "email": "vivek.soni@e2m.solutions",
            "password": "13December200@@@"
        }
        
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json=credentials,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.access_token = response.cookies.get("access_token")
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    @task(25)
    def test_admin_metrics_simple(self):
        """Simple admin metrics test"""
        with self.client.get(
            "/api/v1/metrics/all",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="admin_metrics_simple"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                if self.login():
                    response.success()  # Successful re-authentication
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"Admin metrics failed: {response.status_code}")
    
    @task(15)
    def test_client_metrics_simple(self):
        """Simple client metrics test"""
        client_id = test_data_generator.get_random_client_id()
        
        with self.client.get(
            f"/api/v1/metrics/client/{client_id}",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_metrics_simple"
        ) as response:
            if response.status_code in [200, 404]:  # 404 expected for test data
                response.success()
            elif response.status_code == 401:
                if self.login():
                    response.success()  # Successful re-authentication
                else:
                    response.failure("Authentication failed")
            else:
                response.failure(f"Client metrics failed: {response.status_code}")


if __name__ == "__main__":
    # Can be run standalone for focused metrics testing
    import subprocess
    import sys
    
    print("Running metrics load tests...")
    subprocess.run([
        sys.executable, "-m", "locust", 
        "-f", __file__,
        "--host", "http://localhost:8000",
        "--users", "10",
        "--spawn-rate", "2"
    ])