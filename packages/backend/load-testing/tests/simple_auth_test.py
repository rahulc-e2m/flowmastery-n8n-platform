"""Simple authentication test for load testing verification"""

import json
from locust import HttpUser, task, between


class SimpleAuthUser(HttpUser):
    """Simple authentication test user"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Set up test credentials"""
        # Use the admin credentials that were created
        self.admin_credentials = {
            "email": "vivek.soni@e2m.solutions",
            "password": "13December200@@@"  
        }
    
    @task(10)
    def test_login_logout_cycle(self):
        """Test basic login/logout cycle"""
        # Login
        with self.client.post(
            "/api/v1/auth/login",
            json=self.admin_credentials,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="simple_login"
        ) as response:
            if response.status_code == 200:
                response.success()
                
                # Test getting user info
                with self.client.get(
                    "/api/v1/auth/me",
                    catch_response=True,
                    name="simple_get_me"
                ) as me_response:
                    if me_response.status_code == 200:
                        me_response.success()
                    else:
                        me_response.failure(f"Get me failed: {me_response.status_code}")
                
                # Logout
                with self.client.post(
                    "/api/v1/auth/logout",
                    catch_response=True,
                    name="simple_logout"
                ) as logout_response:
                    if logout_response.status_code == 200:
                        logout_response.success()
                    else:
                        logout_response.failure(f"Logout failed: {logout_response.status_code}")
            else:
                response.failure(f"Login failed: {response.status_code} - {response.text}")
    
    @task(5)
    def test_auth_status(self):
        """Test authentication status check"""
        with self.client.get(
            "/api/v1/auth/status",
            catch_response=True,
            name="simple_auth_status"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "authenticated" in data:
                        response.success()
                    else:
                        response.failure("Missing authenticated field")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Auth status failed: {response.status_code}")