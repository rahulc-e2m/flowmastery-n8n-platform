#!/usr/bin/env python3
"""
Setup script for FlowMastery Backend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def setup_environment():
    """Setup environment file"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        print("📋 Creating .env file from template...")
        shutil.copy2(env_example, env_file)
        print("✅ .env file created")
        print("⚠️  Please edit .env file with your configuration")
        return True
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ .env.example not found")
        return False


def install_dependencies():
    """Install Python dependencies"""
    requirements_file = "requirements/dev.txt"
    if not Path(requirements_file).exists():
        requirements_file = "requirements/base.txt"
    
    if not Path(requirements_file).exists():
        print("❌ Requirements file not found")
        return False
    
    return run_command(
        f"pip install -r {requirements_file}",
        "Installing Python dependencies"
    )


def create_directories():
    """Create necessary directories"""
    directories = ["data", "logs", "tests/test_api", "tests/test_services"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")
    return True


def run_tests():
    """Run basic tests"""
    if not Path("tests").exists():
        print("⚠️  No tests directory found, skipping tests")
        return True
    
    return run_command("python -m pytest tests/ -v", "Running tests")


def check_services():
    """Check if external services are available"""
    print("🔍 Checking external services...")
    
    # Check Redis
    redis_available = run_command(
        "python -c \"import redis; r=redis.Redis(); r.ping()\"",
        "Checking Redis connection"
    )
    
    if not redis_available:
        print("⚠️  Redis not available. Install and start Redis for caching.")
    
    return True


def main():
    """Main setup function"""
    print("🚀 FlowMastery Backend Setup")
    print("=" * 40)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Setting up environment", setup_environment),
        ("Creating directories", create_directories),
        ("Installing dependencies", install_dependencies),
        ("Checking services", check_services),
        ("Running tests", run_tests),
    ]
    
    failed_steps = []
    
    for description, step_func in steps:
        print(f"\n📋 {description}")
        if not step_func():
            failed_steps.append(description)
    
    print("\n" + "=" * 40)
    
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n⚠️  Please resolve the errors above before starting the application.")
        return False
    else:
        print("🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Edit .env file with your configuration")
        print("2. Start the application: python start.py")
        print("3. Visit http://localhost:8000/docs for API documentation")
        print("4. Test the health endpoint: curl http://localhost:8000/health")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)