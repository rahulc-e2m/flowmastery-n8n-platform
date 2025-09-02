"""Main Locust configuration for FlowMastery n8n Platform Load Testing"""

import os
from locust import HttpUser, task, between, events
from locust.env import Environment

# Import test classes
from tests.auth.test_auth_load import AuthLoadUser, ConcurrentAuthUser
from tests.clients.test_client_management import ClientManagementUser, ConcurrentClientOperationsUser

# Import utilities
from config.settings import settings
from utils.auth_helper import AuthHelper
from utils.api_client import APIClient, PerformanceMonitor

# Performance monitoring
performance_monitor = PerformanceMonitor()


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request performance"""
    if exception:
        performance_monitor.error_count += 1
    else:
        performance_monitor.success_count += 1
        performance_monitor.response_times.append(response_time)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment"""
    print(f"Starting FlowMastery Load Tests...")
    print(f"Target URL: {environment.host}")
    print(f"Users: {getattr(environment, 'user_count', 'Not set')}")
    print("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary"""
    stats = performance_monitor.get_stats()
    print("\n" + "=" * 50)
    print("LOAD TEST SUMMARY")
    print("=" * 50)
    
    if stats:
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2%}")
        print(f"Average Response Time: {stats['avg_response_time_ms']:.2f}ms")
        print(f"95th Percentile: {stats['p95_response_time_ms']:.2f}ms")
        print(f"99th Percentile: {stats['p99_response_time_ms']:.2f}ms")
    
    print("=" * 50)


class FlowMasteryLoadUser(HttpUser):
    """Main load testing user that combines multiple test scenarios"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.auth_helper = AuthHelper(self.client)
        self.api_client = APIClient(self.client)
        
        # Login based on user type (admin vs regular user)
        import random
        self.is_admin = random.random() < 0.2  # 20% admin users
        
        if self.is_admin:
            success = self.auth_helper.admin_login()
            if not success:
                print("Failed to login as admin")
        
    @task(30)
    def client_operations(self):
        """Client management operations"""
        if not self.is_admin:
            return
        
        from config.test_data import test_data_generator
        
        # Create client
        client_data = test_data_generator.generate_client_data()
        result = self.api_client.post("/clients/", data=client_data, name="client_create_main")
        
        if result and result.get("success"):
            try:
                client_id = result["response"].json().get("id")
                if client_id:
                    # Get client details
                    self.api_client.get(f"/clients/{client_id}", name="client_get_main")
                    
                    # Configure n8n (30% chance)
                    if self.random.random() < 0.3:
                        n8n_config = test_data_generator.generate_n8n_config()
                        self.api_client.post(
                            f"/clients/{client_id}/n8n-config", 
                            data=n8n_config,
                            name="client_n8n_config_main"
                        )
            except:
                pass
    
    @task(25)
    def authentication_flow(self):
        """Authentication-related operations"""
        # Check auth status
        self.api_client.get("/auth/status", name="auth_status_main")
        
        # Get current user info
        if self.auth_helper.is_authenticated():
            self.api_client.get("/auth/me", name="auth_me_main")
    
    @task(20)
    def metrics_operations(self):
        """Metrics-related operations"""
        if self.is_admin:
            # Admin metrics
            self.api_client.get("/metrics/admin", name="metrics_admin_main")
        else:
            # User metrics
            self.api_client.get("/metrics/my-metrics", name="metrics_my_main")
    
    @task(15)
    def health_checks(self):
        """Health check operations"""
        self.api_client.get("/health/", name="health_basic_main")
        
        # Detailed health check (less frequent)
        if self.random.random() < 0.3:
            self.api_client.get("/health/detailed", name="health_detailed_main")
    
    @task(10)
    def client_listing(self):
        """Client listing operations"""
        if self.is_admin:
            self.api_client.get("/clients/", name="client_list_main")


# User class weights for different scenarios
class LightLoadUser(FlowMasteryLoadUser):
    """Light load testing user"""
    wait_time = between(2, 5)
    weight = 1


class ModerateLoadUser(FlowMasteryLoadUser):
    """Moderate load testing user"""
    wait_time = between(1, 3)
    weight = 2


class HeavyLoadUser(FlowMasteryLoadUser):
    """Heavy load testing user"""
    wait_time = between(0.5, 2)
    weight = 3


# Specialized user types for focused testing
class ClientFocusedUser(ClientManagementUser):
    """User focused on client management operations"""
    weight = 1


class AuthFocusedUser(AuthLoadUser):
    """User focused on authentication operations"""
    weight = 1


class ConcurrentUser(ConcurrentClientOperationsUser):
    """User for concurrent operations testing"""
    weight = 1


# Environment-based user selection
def get_user_classes():
    """Get user classes based on environment or test focus"""
    test_focus = os.getenv("LOAD_TEST_FOCUS", "balanced")
    
    if test_focus == "auth":
        return [AuthLoadUser, ConcurrentAuthUser]
    elif test_focus == "client":
        return [ClientManagementUser, ConcurrentClientOperationsUser]
    elif test_focus == "concurrent":
        return [ConcurrentUser, ConcurrentAuthUser, ConcurrentClientOperationsUser]
    else:  # balanced
        return [FlowMasteryLoadUser, ClientFocusedUser, AuthFocusedUser]


# Default configuration
if __name__ == "__main__":
    # This allows running the file directly
    import subprocess
    import sys
    
    print("FlowMastery Load Testing")
    print("Usage: locust -f locustfile.py --host=http://localhost:8000")
    print("\nAvailable environment variables:")
    print("- LOAD_TEST_FOCUS: auth, client, concurrent, balanced (default)")
    print("- ADMIN_EMAIL: Admin email for testing")
    print("- ADMIN_PASSWORD: Admin password for testing")
    
    # Example run command
    print("\nExample commands:")
    print("locust -f locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 5")
    print("LOAD_TEST_FOCUS=client locust -f locustfile.py --host=http://localhost:8000")
    print("LOAD_TEST_FOCUS=auth locust -f locustfile.py --host=http://localhost:8000 --headless --users 10 --run-time 60s")