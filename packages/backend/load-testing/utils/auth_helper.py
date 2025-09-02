"""Authentication helper utilities for load testing"""

import json
import time
from typing import Dict, Optional, Any
from config.settings import settings


class AuthHelper:
    """Helper class for authentication operations in load tests"""
    
    def __init__(self, client):
        """Initialize with Locust HTTP client"""
        self.client = client
        self.access_token = None
        self.refresh_token = None
        self.login_time = None
        self.user_info = None
    
    def admin_login(self) -> bool:
        """Login as admin user"""
        credentials = {
            "email": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD or "13December200@@@"
        }
        
        return self._perform_login(credentials, "admin_login")
    
    def user_login(self, email: str, password: str) -> bool:
        """Login as regular user"""
        credentials = {
            "email": email,
            "password": password
        }
        
        return self._perform_login(credentials, "user_login")
    
    def _perform_login(self, credentials: Dict[str, str], request_name: str) -> bool:
        """Perform login operation"""
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json=credentials,
                headers={"Content-Type": "application/json"},
                name=request_name
            )
            
            if response.status_code == 200:
                # Store token information from cookies
                self.access_token = response.cookies.get("access_token")
                self.refresh_token = response.cookies.get("refresh_token")
                self.login_time = time.time()
                
                try:
                    response_data = response.json()
                    self.user_info = response_data.get("user", {})
                except json.JSONDecodeError:
                    pass
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token"""
        try:
            response = self.client.post(
                "/api/v1/auth/refresh",
                headers={"Content-Type": "application/json"},
                name="token_refresh"
            )
            
            if response.status_code == 200:
                # Update tokens from cookies
                self.access_token = response.cookies.get("access_token")
                self.refresh_token = response.cookies.get("refresh_token")
                return True
            
            return False
            
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False
    
    def logout(self) -> bool:
        """Logout current user"""
        try:
            response = self.client.post(
                "/api/v1/auth/logout",
                headers={"Content-Type": "application/json"},
                name="logout"
            )
            
            if response.status_code == 200:
                self.access_token = None
                self.refresh_token = None
                self.login_time = None
                self.user_info = None
                return True
            
            return False
            
        except Exception as e:
            print(f"Logout failed: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        if not self.access_token:
            return None
        
        try:
            response = self.client.get(
                "/api/v1/auth/me",
                headers={"Content-Type": "application/json"},
                name="get_current_user"
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Token expired, try to refresh
                if self.refresh_access_token():
                    return self.get_current_user()
            
            return None
            
        except Exception as e:
            print(f"Get current user failed: {e}")
            return None
    
    def check_auth_status(self) -> Dict[str, Any]:
        """Check authentication status"""
        try:
            response = self.client.get(
                "/api/v1/auth/status",
                name="auth_status"
            )
            
            if response.status_code == 200:
                return response.json()
            
            return {"authenticated": False, "error": f"Status code: {response.status_code}"}
            
        except Exception as e:
            return {"authenticated": False, "error": str(e)}
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.access_token is not None
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        if not self.user_info:
            user_data = self.get_current_user()
            if user_data:
                self.user_info = user_data
        
        return self.user_info.get("role") == "admin" if self.user_info else False
    
    def get_client_id(self) -> Optional[str]:
        """Get client ID for current user"""
        if not self.user_info:
            user_data = self.get_current_user()
            if user_data:
                self.user_info = user_data
        
        return self.user_info.get("client_id") if self.user_info else None
    
    def ensure_authenticated(self) -> bool:
        """Ensure user is authenticated, refresh token if needed"""
        if not self.access_token:
            return False
        
        # Check if token is still valid
        current_time = time.time()
        if self.login_time and (current_time - self.login_time) > (settings.PERFORMANCE_THRESHOLDS.get("token_refresh_threshold", 1500)):
            # Token might be close to expiry, refresh it
            return self.refresh_access_token()
        
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers for authenticated requests"""
        headers = {"Content-Type": "application/json"}
        
        # Note: For cookie-based auth, headers don't need token
        # The cookies are automatically included by the client
        
        return headers
    
    def perform_authenticated_request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """Perform an authenticated request with automatic retry on auth failure"""
        if not self.ensure_authenticated():
            return None
        
        # Add auth headers
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update(self.get_auth_headers())
        
        # Perform request
        response = getattr(self.client, method.lower())(endpoint, **kwargs)
        
        # Handle auth failure
        if response.status_code == 401:
            if self.refresh_access_token():
                # Retry with refreshed token
                kwargs["headers"].update(self.get_auth_headers())
                response = getattr(self.client, method.lower())(endpoint, **kwargs)
        
        return response
    
    def cleanup(self):
        """Cleanup authentication state"""
        if self.is_authenticated():
            self.logout()


class SessionManager:
    """Manage multiple user sessions for load testing"""
    
    def __init__(self, client):
        self.client = client
        self.sessions = {}
        self.active_session = None
    
    def create_session(self, session_id: str, email: str, password: str) -> bool:
        """Create a new user session"""
        auth_helper = AuthHelper(self.client)
        success = auth_helper.user_login(email, password)
        
        if success:
            self.sessions[session_id] = auth_helper
            return True
        
        return False
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different user session"""
        if session_id in self.sessions:
            self.active_session = session_id
            return True
        return False
    
    def get_current_session(self) -> Optional[AuthHelper]:
        """Get current active session"""
        if self.active_session and self.active_session in self.sessions:
            return self.sessions[self.active_session]
        return None
    
    def cleanup_all_sessions(self):
        """Cleanup all sessions"""
        for session in self.sessions.values():
            session.cleanup()
        self.sessions.clear()
        self.active_session = None