"""Development startup script"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting FlowMastery Backend Development Environment")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file from .env.example...")
        try:
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ .env file created. Please update it with your configuration.")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return
    
    # Start database and Redis with Docker Compose
    if not run_command("docker-compose -f docker-compose.dev.yml up -d", "Starting PostgreSQL and Redis"):
        print("❌ Failed to start database services")
        return
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    import time
    time.sleep(5)
    
    # Run database migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        print("⚠️  Database migrations failed, but continuing...")
    
    # Check if admin user exists, if not, prompt to create one
    print("👤 Checking for admin user...")
    try:
        result = subprocess.run([sys.executable, "create_admin.py"], capture_output=True, text=True)
        if "already exists" not in result.stdout and "created successfully" not in result.stdout:
            print("ℹ️  You may need to create an admin user manually by running: python create_admin.py")
    except Exception as e:
        print(f"ℹ️  To create an admin user, run: python create_admin.py")
    
    # Start the FastAPI server
    print("🌟 Starting FastAPI server...")
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        run_command("docker-compose -f docker-compose.dev.yml down", "Stopping services")

if __name__ == "__main__":
    main()