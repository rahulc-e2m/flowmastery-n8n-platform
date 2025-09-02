"""Authentication endpoint load testing"""

import json
import random
from locust import HttpUser, task, between, SequentialTaskSet
from locust.exception import ResponseError

from config.settings import settings, get_endpoint_url
from config.test_data import test_data_generator
from utils.auth_helper import AuthHelper
from utils.api_client import APIClient


class AuthLoadTaskSet(SequentialTaskSet):
    """Sequential authentication load testing tasks"""
    
    def on_start(self):
        """Initialize test data for this user"""
        self.auth_helper = AuthHelper(self.client)
        self.api_client = APIClient(self.client)
        
        # Generate test credentials
        self.admin_credentials = {
            "email": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD or "13December200@@@"
        }
        
        self.user_credentials = test_data_generator.generate_login_credentials()
        self.access_token = None
        self.refresh_token = None
    
    @task(10)
    def test_admin_login(self):
        """Test admin user login performance"""
        with self.client.post(
            "/api/v1/auth/login",
            json=self.admin_credentials,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="auth_admin_login"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Store token information (even if empty in response body)
                    self.access_token = response.cookies.get("access_token")
                    response.success()
                except (json.JSONDecodeError, KeyError) as e:
                    response.failure(f"Login response parsing failed: {e}")
            else:
                response.failure(f"Login failed with status {response.status_code}")
    
    @task(5)
    def test_token_refresh(self):
        """Test token refresh performance"""
        if not self.access_token:
            return
        
        with self.client.post(
            "/api/v1/auth/refresh",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="auth_token_refresh"
        ) as response:
            if response.status_code == 200:
                try:
                    # Update token from cookies
                    self.access_token = response.cookies.get("access_token")
                    response.success()
                except Exception as e:
                    response.failure(f"Token refresh failed: {e}")
            else:
                response.failure(f"Token refresh failed with status {response.status_code}")
    
    @task(8)
    def test_get_current_user(self):
        """Test getting current user information"""
        if not self.access_token:
            return
        
        with self.client.get(
            "/api/v1/auth/me",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="auth_get_current_user"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "email" in data:
                        response.success()
                    else:
                        response.failure("User data incomplete")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                # Token might be expired, try to refresh
                self.test_token_refresh()
            else:
                response.failure(f"Get user info failed with status {response.status_code}")
    
    @task(3)
    def test_auth_status(self):
        """Test authentication status check"""
        with self.client.get(
            "/api/v1/auth/status",
            catch_response=True,
            name="auth_status_check"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "authenticated" in data:
                        response.success()
                    else:
                        response.failure("Status response incomplete")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Auth status failed with status {response.status_code}")
    
    @task(2)
    def test_logout(self):
        """Test logout performance"""
        if not self.access_token:
            return
        
        with self.client.post(
            "/api/v1/auth/logout",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="auth_logout"
        ) as response:
            if response.status_code == 200:
                self.access_token = None
                self.refresh_token = None
                response.success()
            else:
                response.failure(f"Logout failed with status {response.status_code}")
    
    # Remove wait_time method to use class-level wait_time


class AuthLoadUser(HttpUser):
    """Authentication load testing user"""
    
    tasks = [AuthLoadTaskSet]
    wait_time = between(1, 5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_helper = None
    
    def on_start(self):
        """Initialize user session"""
        self.auth_helper = AuthHelper(self.client)
        
        # Perform initial login to establish session
        try:
            self.auth_helper.admin_login()
        except Exception as e:
            print(f"Initial login failed: {e}")


class ConcurrentAuthUser(HttpUser):
    """Concurrent authentication testing user"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Setup for concurrent testing"""
        self.credentials = test_data_generator.generate_login_credentials(
            is_admin=random.random() < 0.1  # 10% admin users
        )
    
    @task(20)
    def rapid_login_logout(self):
        """Rapid login/logout cycle for stress testing"""
        # Login
        login_response = self.client.post(
            "/api/v1/auth/login",
            json=self.credentials,
            name="concurrent_login"
        )
        
        if login_response.status_code == 200:
            # Quick authenticated request
            self.client.get("/api/v1/auth/me", name="concurrent_me_check")
            
            # Logout
            self.client.post("/api/v1/auth/logout", name="concurrent_logout")
    
    @task(10)
    def session_management(self):
        """Test session management under load"""
        # Login
        login_response = self.client.post(
            "/api/v1/auth/login", 
            json=self.credentials,
            name="session_login"
        )
        
        if login_response.status_code == 200:
            # Multiple authenticated requests
            for _ in range(random.randint(3, 8)):
                self.client.get("/api/v1/auth/status", name="session_status_check")
                self.wait()
            
            # Token refresh
            self.client.post("/api/v1/auth/refresh", name="session_refresh")
            
            # Final logout
            self.client.post("/api/v1/auth/logout", name="session_logout")
    
    @task(5)
    def invalid_auth_attempts(self):
        """Test handling of invalid authentication attempts"""
        invalid_credentials = {
            "email": test_data_generator.fake.email(),
            "password": "WrongPassword123!"
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=invalid_credentials,
            catch_response=True,
            name="invalid_auth_attempt"
        ) as response:
            if response.status_code == 401:
                response.success()  # Expected failure
            else:
                response.failure(f"Unexpected status: {response.status_code}")


# Rate limiting test user
class RateLimitTestUser(HttpUser):
    """Test rate limiting on authentication endpoints"""
    
    wait_time = between(0.1, 0.5)  # Very fast requests to trigger rate limiting
    
    def on_start(self):
        self.credentials = test_data_generator.generate_login_credentials()
    
    @task(30)
    def rapid_fire_login(self):
        """Rapid fire login attempts to test rate limiting"""
        with self.client.post(
            "/api/v1/auth/login",
            json=self.credentials,
            catch_response=True,
            name="rate_limit_login_test"
        ) as response:
            if response.status_code == 429:  # Too Many Requests
                response.success()  # Rate limiting is working
            elif response.status_code in [200, 401]:
                response.success()  # Normal response
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(10)
    def rapid_fire_refresh(self):
        """Rapid fire refresh attempts to test rate limiting"""
        with self.client.post(
            "/api/v1/auth/refresh",
            catch_response=True,
            name="rate_limit_refresh_test"
        ) as response:
            if response.status_code in [429, 401, 200]:  # Expected responses
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


if __name__ == "__main__":
    # Can be run standalone for focused auth testing
    import subprocess
    import sys
    
    print("Running authentication load tests...")
    subprocess.run([
        sys.executable, "-m", "locust", 
        "-f", __file__,
        "--host", settings.BASE_URL,
        "--users", str(settings.DEFAULT_USERS),
        "--spawn-rate", str(settings.DEFAULT_SPAWN_RATE)
    ])