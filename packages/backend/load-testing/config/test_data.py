"""Test data generators for load testing"""

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from faker import Faker

fake = Faker()


class TestDataGenerator:
    """Generate test data for load testing"""
    
    def __init__(self):
        self.fake = Faker()
        self.generated_clients = []
        self.generated_users = []
    
    def generate_client_data(self) -> Dict[str, Any]:
        """Generate realistic client data"""
        company_name = self.fake.company()
        return {
            "name": company_name,
            "description": f"Test client for {company_name}",
            "industry": self.fake.random_element([
                "Technology", "Healthcare", "Finance", "Manufacturing", 
                "Retail", "Education", "Government", "Non-profit"
            ]),
            "size": self.fake.random_element(["Small", "Medium", "Large", "Enterprise"]),
            "created_by_test": True
        }
    
    def generate_user_data(self, client_id: str = None) -> Dict[str, Any]:
        """Generate realistic user data"""
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        email = self.fake.email()
        
        return {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "password": "TestPassword123!",
            "role": self.fake.random_element(["client_user", "client_admin"]),
            "client_id": client_id,
            "is_active": True
        }
    
    def generate_n8n_config(self) -> Dict[str, Any]:
        """Generate n8n configuration data"""
        return {
            "n8n_api_url": f"https://n8n-{self.fake.uuid4()[:8]}.example.com/api/v1",
            "n8n_api_key": self.fake.uuid4()
        }
    
    def generate_login_credentials(self, is_admin: bool = False) -> Dict[str, str]:
        """Generate login credentials"""
        if is_admin:
            return {
                "email": "vivek.soni@e2m.solutions",
                "password": "AdminPassword123!"  # This should match your actual admin password
            }
        else:
            return {
                "email": self.fake.email(),
                "password": "TestPassword123!"
            }
    
    def generate_bulk_clients(self, count: int) -> List[Dict[str, Any]]:
        """Generate multiple client records"""
        clients = []
        for _ in range(count):
            client_data = self.generate_client_data()
            clients.append(client_data)
            self.generated_clients.append(client_data)
        return clients
    
    def generate_bulk_users(self, count: int, client_id: str = None) -> List[Dict[str, Any]]:
        """Generate multiple user records"""
        users = []
        for _ in range(count):
            user_data = self.generate_user_data(client_id)
            users.append(user_data)
            self.generated_users.append(user_data)
        return users
    
    def generate_metrics_query_params(self) -> Dict[str, Any]:
        """Generate realistic metrics query parameters"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=random.randint(7, 90))
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "period_type": random.choice(["DAILY", "WEEKLY", "MONTHLY"]),
            "workflow_id": random.randint(1, 100) if random.random() > 0.7 else None
        }
    
    def generate_execution_query_params(self) -> Dict[str, Any]:
        """Generate execution query parameters"""
        return {
            "limit": random.randint(10, 100),
            "offset": random.randint(0, 500),
            "status": random.choice(["SUCCESS", "ERROR", "RUNNING", None]),
            "workflow_id": random.randint(1, 50) if random.random() > 0.5 else None
        }
    
    def generate_workflow_data(self, client_id: str) -> Dict[str, Any]:
        """Generate workflow data for testing"""
        return {
            "name": f"Test Workflow {self.fake.uuid4()[:8]}",
            "n8n_workflow_id": str(random.randint(1000, 9999)),
            "description": self.fake.text(max_nb_chars=200),
            "active": random.choice([True, False]),
            "client_id": client_id,
            "time_saved_per_execution_minutes": random.randint(5, 120),
            "category": random.choice([
                "Data Processing", "Integration", "Automation", 
                "Notification", "Analytics", "API Management"
            ])
        }
    
    def generate_test_scenario_data(self, scenario_type: str) -> Dict[str, Any]:
        """Generate data for specific test scenarios"""
        scenarios = {
            "peak_traffic": {
                "concurrent_users": random.randint(50, 200),
                "requests_per_second": random.randint(100, 500),
                "duration_minutes": random.randint(10, 30)
            },
            "client_management": {
                "clients_to_create": random.randint(5, 20),
                "users_per_client": random.randint(3, 10),
                "operations_per_minute": random.randint(10, 50)
            },
            "metrics_heavy": {
                "metrics_queries_per_user": random.randint(10, 50),
                "historical_data_range_days": random.randint(30, 365),
                "concurrent_metrics_users": random.randint(20, 100)
            },
            "n8n_integration": {
                "n8n_configs_to_test": random.randint(5, 15),
                "sync_operations_per_client": random.randint(3, 10),
                "connection_tests_per_minute": random.randint(5, 20)
            }
        }
        
        return scenarios.get(scenario_type, {})
    
    def get_random_client_id(self) -> str:
        """Get a random client ID from generated clients"""
        if not self.generated_clients:
            return str(uuid.uuid4())
        return str(uuid.uuid4())  # In real scenario, this would be from actual created clients
    
    def get_random_user_email(self) -> str:
        """Get a random user email from generated users"""
        if not self.generated_users:
            return self.fake.email()
        return random.choice(self.generated_users)["email"]
    
    def cleanup_generated_data(self):
        """Clear generated data"""
        self.generated_clients.clear()
        self.generated_users.clear()


# Global test data generator instance
test_data_generator = TestDataGenerator()


# Pre-defined test data sets
SAMPLE_CLIENTS = [
    {
        "name": "Acme Corporation",
        "description": "Global technology solutions provider"
    },
    {
        "name": "TechStart Innovations", 
        "description": "Startup focused on AI and automation"
    },
    {
        "name": "Enterprise Solutions Ltd",
        "description": "Large enterprise software company"
    },
    {
        "name": "Digital Transformation Co",
        "description": "Digital transformation consultancy"
    },
    {
        "name": "Automation Masters Inc",
        "description": "Workflow automation specialists"
    }
]

SAMPLE_N8N_CONFIGS = [
    {
        "n8n_api_url": "https://n8n-prod.example.com/api/v1",
        "n8n_api_key": "test-api-key-1"
    },
    {
        "n8n_api_url": "https://n8n-staging.example.com/api/v1", 
        "n8n_api_key": "test-api-key-2"
    },
    {
        "n8n_api_url": "https://n8n-dev.example.com/api/v1",
        "n8n_api_key": "test-api-key-3"
    }
]

# Load testing specific data
LOAD_TEST_PATTERNS = {
    "gradual_ramp": [1, 2, 5, 10, 20, 30, 50, 75, 100],
    "spike_test": [1, 1, 1, 100, 100, 100, 1, 1, 1],
    "steady_state": [50] * 10,
    "stress_test": [10, 25, 50, 100, 150, 200, 250, 300, 350, 400]
}

def get_load_pattern(pattern_name: str) -> List[int]:
    """Get predefined load testing pattern"""
    return LOAD_TEST_PATTERNS.get(pattern_name, [10, 20, 30, 40, 50])