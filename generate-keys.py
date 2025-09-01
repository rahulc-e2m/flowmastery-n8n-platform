#!/usr/bin/env python3
"""
Security Key Generator
Generates cryptographically secure keys for FlowMastery platform
"""

import secrets
import os
import sys
from pathlib import Path


def generate_secret_key() -> str:
    """Generate a 64-character hex string for SECRET_KEY"""
    return secrets.token_hex(32)


def generate_encryption_key() -> str:
    """Generate a 32-character string for ENCRYPTION_KEY"""
    return secrets.token_urlsafe(32)[:32]


def create_env_file():
    """Create a .env file with secure keys"""
    project_root = Path(__file__).parent
    env_example_path = project_root / ".env.example"
    env_path = project_root / ".env"
    
    if not env_example_path.exists():
        print("❌ .env.example file not found!")
        sys.exit(1)
    
    if env_path.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✅ Keeping existing .env file")
            return
    
    # Generate secure keys
    secret_key = generate_secret_key()
    encryption_key = generate_encryption_key()
    
    # Read .env.example and replace placeholders
    with open(env_example_path, 'r') as f:
        content = f.read()
    
    # Replace placeholders with actual keys
    content = content.replace(
        "CHANGE_ME_GENERATE_WITH_PYTHON_SECRETS_TOKEN_HEX_32_EXACTLY_64_CHARS",
        secret_key
    )
    content = content.replace(
        "your-32-char-encryption-key-here!!",
        encryption_key + "!!"  # Keep the !! at the end
    )
    
    # Ask for production domain if this is for production
    if "production" in content.lower() or "prod" in content.lower():
        production_hosts = input("Enter production hostnames (comma-separated, e.g., yourdomain.com,api.yourdomain.com): ").strip()
        if production_hosts:
            content = content.replace(
                "localhost,127.0.0.1,0.0.0.0",
                production_hosts
            )
    
    # Write to .env
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("✅ Generated .env file with secure keys!")
    print(f"📝 SECRET_KEY: {secret_key[:16]}...{secret_key[-16:]} (64 chars)")
    print(f"🔐 ENCRYPTION_KEY: {encryption_key}!! (32 chars)")
    print("")
    print("🚨 IMPORTANT SECURITY NOTES:")
    print("1. These keys are cryptographically secure")
    print("2. Never commit .env file to version control")
    print("3. Use different keys for each environment")
    print("4. Backup these keys securely")
    print("5. Rotate keys periodically")


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "keys-only":
        print("🔑 Generated Keys:")
        print(f"SECRET_KEY={generate_secret_key()}")
        print(f"ENCRYPTION_KEY={generate_encryption_key()}!!")
    else:
        print("🔐 FlowMastery Security Key Generator")
        print("=" * 40)
        create_env_file()


if __name__ == "__main__":
    main()