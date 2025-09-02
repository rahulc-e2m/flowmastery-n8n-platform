#!/usr/bin/env python3
"""Setup test data and validate load testing environment"""

import sys
import os
import asyncio
import json
import requests
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings, API_ENDPOINTS
from config.test_data import test_data_generator
from utils.auth_helper import AuthHelper


class LoadTestSetup:
    """Setup and validate load testing environment"""
    
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.api_base_url = settings.api_base_url
        self.session = requests.Session()
        self.access_token = None
    
    def check_backend_connectivity(self):
        """Check if backend is running and accessible"""
        print("🔍 Checking backend connectivity...")
        
        try:
            # Basic health check
            response = self.session.get(f"{self.base_url}/health/")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Backend health check passed")
                    return True
            
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
            
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to backend. Is it running?")
            return False
        except Exception as e:
            print(f"❌ Backend connectivity error: {e}")
            return False
    
    def check_api_endpoints(self):
        """Check if API endpoints are accessible"""
        print("🔍 Checking API endpoints...")
        
        try:
            # Check auth status endpoint
            response = self.session.get(f"{self.api_base_url}/auth/status")
            if response.status_code == 200:
                print("✅ Auth endpoints accessible")
            else:
                print(f"⚠️ Auth endpoints returned: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ API endpoints error: {e}")
            return False
    
    def test_admin_authentication(self):
        """Test admin authentication"""
        print("🔑 Testing admin authentication...")
        
        try:
            login_data = {
                "email": settings.ADMIN_EMAIL,
                "password": settings.ADMIN_PASSWORD or "AdminPassword123!"
            }
            
            response = self.session.post(
                f"{self.api_base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.access_token = response.cookies.get("access_token")
                if self.access_token:
                    print("✅ Admin authentication successful")
                    return True
                else:
                    print("⚠️ Login successful but no access token in cookies")
                    return True
            else:
                print(f"❌ Admin authentication failed: {response.status_code}")
                if response.status_code == 401:
                    print("💡 Please check ADMIN_EMAIL and ADMIN_PASSWORD in config/settings.py")
                return False
                
        except Exception as e:
            print(f"❌ Admin authentication error: {e}")
            return False
    
    def test_client_api_access(self):
        """Test client API access"""
        print("🏢 Testing client API access...")
        
        if not self.access_token:
            print("⚠️ Skipping client API test (no auth token)")
            return False
        
        try:
            # Test client listing
            response = self.session.get(
                f"{self.api_base_url}/clients/",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                clients = response.json()
                print(f"✅ Client API accessible (found {len(clients)} clients)")
                return True
            elif response.status_code == 401:
                print("⚠️ Client API authentication issue")
                return False
            else:
                print(f"❌ Client API access failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Client API error: {e}")
            return False
    
    def create_test_client(self):
        """Create a test client for load testing"""
        print("🔧 Creating test client...")
        
        if not self.access_token:
            print("⚠️ Skipping test client creation (no auth token)")
            return None
        
        try:
            client_data = test_data_generator.generate_client_data()
            client_data["name"] = "Load Test Client - " + client_data["name"]
            
            response = self.session.post(
                f"{self.api_base_url}/clients/",
                json=client_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                client = response.json()
                client_id = client.get("id")
                print(f"✅ Test client created: {client_id}")
                return client_id
            else:
                print(f"❌ Test client creation failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Test client creation error: {e}")
            return None
    
    def validate_environment_config(self):
        """Validate environment configuration"""
        print("⚙️ Validating environment configuration...")
        
        issues = []
        
        # Check required settings
        if not settings.ADMIN_EMAIL:
            issues.append("ADMIN_EMAIL not configured")
        
        if not settings.ADMIN_PASSWORD:
            issues.append("ADMIN_PASSWORD not configured")
        
        if settings.BASE_URL == "http://localhost:8000":
            print("ℹ️ Using default backend URL (localhost:8000)")
        
        # Check performance thresholds
        thresholds = settings.PERFORMANCE_THRESHOLDS
        if thresholds.get("auth_login_max_time", 0) == 0:
            issues.append("Performance thresholds not properly configured")
        
        if issues:
            print("⚠️ Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Environment configuration validated")
            return True
    
    def generate_sample_test_data(self):
        """Generate sample test data for load testing"""
        print("📊 Generating sample test data...")
        
        try:
            # Generate clients
            clients = test_data_generator.generate_bulk_clients(5)
            print(f"✅ Generated {len(clients)} sample clients")
            
            # Generate users
            users = test_data_generator.generate_bulk_users(10)
            print(f"✅ Generated {len(users)} sample users")
            
            # Generate n8n configs
            n8n_configs = [test_data_generator.generate_n8n_config() for _ in range(3)]
            print(f"✅ Generated {len(n8n_configs)} n8n configurations")
            
            return True
            
        except Exception as e:
            print(f"❌ Sample data generation error: {e}")
            return False
    
    def run_connectivity_test(self):
        """Run a quick connectivity test"""
        print("🚀 Running connectivity test...")
        
        try:
            # Test multiple rapid requests
            success_count = 0
            total_requests = 10
            
            for i in range(total_requests):
                response = self.session.get(f"{self.base_url}/health/")
                if response.status_code == 200:
                    success_count += 1
            
            success_rate = success_count / total_requests
            print(f"✅ Connectivity test: {success_count}/{total_requests} requests successful ({success_rate:.1%})")
            
            return success_rate > 0.8
            
        except Exception as e:
            print(f"❌ Connectivity test error: {e}")
            return False
    
    def cleanup_test_data(self, client_id):
        """Cleanup test data"""
        if client_id and self.access_token:
            try:
                response = self.session.delete(f"{self.api_base_url}/clients/{client_id}")
                if response.status_code == 200:
                    print(f"🧹 Cleaned up test client: {client_id}")
            except:
                pass  # Ignore cleanup errors
    
    def run_full_setup(self):
        """Run complete setup and validation"""
        print("🏁 Starting FlowMastery Load Testing Setup")
        print("=" * 50)
        
        steps = [
            ("Backend Connectivity", self.check_backend_connectivity),
            ("API Endpoints", self.check_api_endpoints),
            ("Environment Config", self.validate_environment_config),
            ("Admin Authentication", self.test_admin_authentication),
            ("Client API Access", self.test_client_api_access),
            ("Sample Data Generation", self.generate_sample_test_data),
            ("Connectivity Test", self.run_connectivity_test),
        ]
        
        passed_steps = 0
        test_client_id = None
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if step_func():
                passed_steps += 1
            else:
                print(f"❌ Step failed: {step_name}")
        
        # Create test client if auth worked
        if passed_steps >= 4:  # If auth steps passed
            test_client_id = self.create_test_client()
        
        print("\n" + "=" * 50)
        print(f"🏆 Setup Summary: {passed_steps}/{len(steps)} steps passed")
        
        if passed_steps == len(steps):
            print("✅ All setup steps completed successfully!")
            print("🚀 Ready to run load tests!")
            
            print("\n🎯 Next steps:")
            print("1. Run quick test: ./scripts/run_client_tests.sh quick")
            print("2. Run full suite: ./scripts/run_client_tests.sh all")
            print("3. Open Locust UI: locust -f locustfile.py --host=http://localhost:8000")
            
        elif passed_steps >= 4:
            print("⚠️ Setup completed with some warnings")
            print("🚀 Load testing should work, but check warnings above")
            
        else:
            print("❌ Setup failed - please fix errors before running load tests")
            
        # Cleanup
        if test_client_id:
            self.cleanup_test_data(test_client_id)
        
        return passed_steps == len(steps)


def main():
    """Main setup function"""
    setup = LoadTestSetup()
    success = setup.run_full_setup()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()