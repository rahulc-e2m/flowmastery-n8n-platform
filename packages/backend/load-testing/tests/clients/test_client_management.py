"""Client management API load testing"""

import json
import random
import uuid
from locust import HttpUser, task, between, SequentialTaskSet
from locust.exception import ResponseError

from config.settings import settings, get_endpoint_url
from config.test_data import test_data_generator, SAMPLE_CLIENTS
from utils.auth_helper import AuthHelper
from utils.api_client import APIClient


class ClientManagementTaskSet(SequentialTaskSet):
    """Sequential client management operations for load testing"""
    
    def on_start(self):
        """Initialize test session"""
        self.auth_helper = AuthHelper(self.client)
        self.api_client = APIClient(self.client)
        self.created_clients = []
        
        # Login as admin for client management operations
        success = self.auth_helper.admin_login()
        if not success:
            print("Failed to login as admin for client management tests")
    
    @task(15)
    def test_create_client(self):
        """Test client creation performance"""
        client_data = test_data_generator.generate_client_data()
        
        with self.client.post(
            "/api/v1/clients/",
            json=client_data,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_create"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    client_id = data.get("id")
                    if client_id:
                        self.created_clients.append(client_id)
                        response.success()
                    else:
                        response.failure("No client ID in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                # Re-authenticate and retry
                self.auth_helper.admin_login()
                response.failure("Authentication expired during client creation")
            else:
                response.failure(f"Client creation failed with status {response.status_code}")
    
    @task(25)
    def test_list_clients(self):
        """Test client listing performance"""
        with self.client.get(
            "/api/v1/clients/",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_list"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Expected list response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                self.auth_helper.admin_login()
                response.failure("Authentication expired during client listing")
            else:
                response.failure(f"Client listing failed with status {response.status_code}")
    
    @task(20)
    def test_get_client_details(self):
        """Test individual client retrieval performance"""
        if not self.created_clients:
            # Create a client first
            self.test_create_client()
            return
        
        client_id = random.choice(self.created_clients)
        
        with self.client.get(
            f"/api/v1/clients/{client_id}",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_get_details"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("id") == client_id:
                        response.success()
                    else:
                        response.failure("Client ID mismatch")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                # Client might have been deleted, remove from our list
                self.created_clients.remove(client_id)
                response.failure("Client not found")
            elif response.status_code == 401:
                self.auth_helper.admin_login()
                response.failure("Authentication expired")
            else:
                response.failure(f"Get client failed with status {response.status_code}")
    
    @task(10)
    def test_configure_n8n_api(self):
        """Test n8n API configuration performance"""
        if not self.created_clients:
            self.test_create_client()
            return
        
        client_id = random.choice(self.created_clients)
        n8n_config = test_data_generator.generate_n8n_config()
        
        with self.client.post(
            f"/api/v1/clients/{client_id}/n8n-config",
            json=n8n_config,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_n8n_config"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("client_id") == client_id:
                        response.success()
                    else:
                        response.failure("Client ID mismatch in n8n config response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.failure("Client not found for n8n config")
            elif response.status_code == 401:
                self.auth_helper.admin_login()
                response.failure("Authentication expired")
            else:
                response.failure(f"n8n config failed with status {response.status_code}")
    
    @task(5)
    def test_n8n_connection_test(self):
        """Test n8n connection testing performance"""
        n8n_config = test_data_generator.generate_n8n_config()
        
        with self.client.post(
            "/api/v1/clients/test-n8n-connection",
            json=n8n_config,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_n8n_test"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "status" in data and "connection_healthy" in data:
                        response.success()
                    else:
                        response.failure("Incomplete n8n test response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                self.auth_helper.admin_login()
                response.failure("Authentication expired")
            else:
                response.failure(f"n8n test failed with status {response.status_code}")
    
    @task(8)
    def test_trigger_n8n_sync(self):
        """Test n8n data sync trigger performance"""
        if not self.created_clients:
            self.test_create_client()
            return
        
        client_id = random.choice(self.created_clients)
        
        with self.client.post(
            f"/api/v1/clients/{client_id}/sync-n8n",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_n8n_sync"
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
            elif response.status_code == 400:
                # Expected if n8n not configured
                response.success()
            elif response.status_code == 404:
                response.failure("Client not found for sync")
            elif response.status_code == 401:
                self.auth_helper.admin_login()
                response.failure("Authentication expired")
            else:
                response.failure(f"n8n sync failed with status {response.status_code}")
    
    @task(3)
    def test_delete_client(self):
        """Test client deletion performance"""
        if len(self.created_clients) <= 1:
            # Keep at least one client for other operations
            return
        
        client_id = self.created_clients.pop()  # Remove and delete
        
        with self.client.delete(
            f"/api/v1/clients/{client_id}",
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="client_delete"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Client not found for deletion")
            elif response.status_code == 401:
                self.auth_helper.admin_login()
                response.failure("Authentication expired")
            else:
                response.failure(f"Client deletion failed with status {response.status_code}")
    
    def on_stop(self):
        """Cleanup created test clients"""
        for client_id in self.created_clients:
            try:
                self.client.delete(f"/api/v1/clients/{client_id}")
            except:
                pass  # Ignore cleanup errors


class ClientManagementUser(HttpUser):
    """Client management load testing user"""
    
    tasks = [ClientManagementTaskSet]
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.auth_helper = AuthHelper(self.client)


class ConcurrentClientOperationsUser(HttpUser):
    """Concurrent client operations testing"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Setup concurrent testing"""
        self.auth_helper = AuthHelper(self.client)
        self.auth_helper.admin_login()
        self.test_clients = []
    
    @task(20)
    def rapid_client_operations(self):
        """Rapid client CRUD operations"""
        # Create client
        client_data = test_data_generator.generate_client_data()
        create_response = self.client.post(
            "/api/v1/clients/",
            json=client_data,
            name="concurrent_client_create"
        )
        
        if create_response.status_code == 200:
            try:
                client_id = create_response.json().get("id")
                if client_id:
                    self.test_clients.append(client_id)
                    
                    # Immediate read after create
                    self.client.get(
                        f"/api/v1/clients/{client_id}",
                        name="concurrent_client_read"
                    )
                    
                    # Configure n8n if we have clients
                    if random.random() < 0.3:  # 30% chance
                        n8n_config = test_data_generator.generate_n8n_config()
                        self.client.post(
                            f"/api/v1/clients/{client_id}/n8n-config",
                            json=n8n_config,
                            name="concurrent_n8n_config"
                        )
            except:
                pass
    
    @task(15)
    def bulk_client_listing(self):
        """Bulk client listing operations"""
        # Multiple rapid list requests
        for _ in range(random.randint(3, 7)):
            self.client.get("/api/v1/clients/", name="bulk_client_list")
    
    @task(5)
    def cleanup_test_clients(self):
        """Periodically cleanup test clients"""
        if len(self.test_clients) > 10:  # Keep some, cleanup excess
            clients_to_delete = self.test_clients[:5]
            self.test_clients = self.test_clients[5:]
            
            for client_id in clients_to_delete:
                self.client.delete(
                    f"/api/v1/clients/{client_id}",
                    name="concurrent_client_cleanup"
                )


class ClientAccessControlUser(HttpUser):
    """Test client access control under load"""
    
    wait_time = between(1, 4)
    
    def on_start(self):
        """Setup access control testing"""
        self.auth_helper = AuthHelper(self.client)
        
        # Sometimes login as admin, sometimes as regular user
        if random.random() < 0.3:  # 30% admin users
            self.auth_helper.admin_login()
            self.is_admin = True
        else:
            # For this test, we'll simulate regular user access
            self.is_admin = False
    
    @task(30)
    def test_client_access_patterns(self):
        """Test different client access patterns"""
        if self.is_admin:
            # Admin can access all client operations
            self.client.get("/api/v1/clients/", name="admin_client_list")
            
            # Test client creation
            client_data = test_data_generator.generate_client_data()
            self.client.post(
                "/api/v1/clients/",
                json=client_data,
                name="admin_client_create"
            )
        else:
            # Regular user access patterns
            fake_client_id = str(uuid.uuid4())
            
            # Should get forbidden for admin operations
            with self.client.get(
                "/api/v1/clients/",
                catch_response=True,
                name="user_client_list_forbidden"
            ) as response:
                if response.status_code in [401, 403]:
                    response.success()  # Expected forbidden
                else:
                    response.failure(f"Unexpected access granted: {response.status_code}")
            
            # Should get forbidden for client creation
            client_data = test_data_generator.generate_client_data()
            with self.client.post(
                "/api/v1/clients/",
                json=client_data,
                catch_response=True,
                name="user_client_create_forbidden"
            ) as response:
                if response.status_code in [401, 403]:
                    response.success()  # Expected forbidden
                else:
                    response.failure(f"Unexpected access granted: {response.status_code}")


if __name__ == "__main__":
    # Standalone execution
    import subprocess
    import sys
    
    print("Running client management load tests...")
    subprocess.run([
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--host", settings.BASE_URL,
        "--users", "20",
        "--spawn-rate", "5"
    ])