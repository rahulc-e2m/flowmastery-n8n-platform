#!/usr/bin/env python3
"""
Test script for validating the persistent metrics system in Docker
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test if the API is healthy"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def test_database_migration():
    """Test if database tables exist"""
    print("🔍 Testing Database Migration...")
    try:
        # This endpoint should return data if tables exist
        response = requests.get(f"{BASE_URL}/api/v1/metrics/all", timeout=10)
        if response.status_code in [200, 404]:  # 404 is OK if no data yet
            print("✅ Database tables appear to be created")
            return True
        else:
            print(f"❌ Database migration issue: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_celery_worker():
    """Test if Celery worker is responding"""
    print("🔍 Testing Celery Worker...")
    try:
        # Trigger a health check task
        response = requests.post(f"{BASE_URL}/api/v1/tasks/health-check", timeout=10)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ Health check task started: {task_id}")
            
            # Wait a moment and check task status
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/v1/tasks/status/{task_id}", timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Task status retrieved: {status_data['status']}")
                return True
            else:
                print(f"⚠️ Task status check failed: {status_response.status_code}")
                return False
        else:
            print(f"❌ Celery task trigger failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Celery test failed: {e}")
        return False

def test_worker_stats():
    """Test worker statistics endpoint"""
    print("🔍 Testing Worker Statistics...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tasks/worker-stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            workers = data.get('workers', {})
            if workers:
                print(f"✅ Found {len(workers)} active workers")
                for worker_name in workers.keys():
                    print(f"   - Worker: {worker_name}")
                return True
            else:
                print("⚠️ No active workers found (this might be expected)")
                return True
        else:
            print(f"❌ Worker stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Worker stats test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Docker Deployment Test Suite")
    print("=" * 50)
    
    tests = [
        ("API Health", test_api_health),
        ("Database Migration", test_database_migration),
        ("Celery Worker", test_celery_worker),
        ("Worker Statistics", test_worker_stats)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your persistent metrics system is working in Docker!")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print("\n🔗 Useful URLs:")
    print(f"   - API Documentation: {BASE_URL}/docs")
    print(f"   - Celery Flower: http://localhost:5555")
    print(f"   - Frontend: http://localhost:3000")

if __name__ == "__main__":
    main()