"""Script to create the first admin user"""

import asyncio
import sys
from getpass import getpass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User
from app.core.auth import get_password_hash


async def create_admin_user():
    """Create the first admin user"""
    print("🔧 Creating first admin user...")
    
    # Get user input
    email = input("Enter admin email: ").strip()
    if not email:
        print("❌ Email is required")
        return
    
    password = getpass("Enter admin password (min 12 chars, uppercase, lowercase, digit, special char): ").strip()
    if len(password) < 12:
        print("❌ Password must be at least 12 characters")
        return
    
    # Validate password strength
    import re
    if not re.search(r'[A-Z]', password):
        print("❌ Password must contain at least one uppercase letter")
        return
    if not re.search(r'[a-z]', password):
        print("❌ Password must contain at least one lowercase letter")
        return
    if not re.search(r'\d', password):
        print("❌ Password must contain at least one digit")
        return
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        print("❌ Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
        return
    
    confirm_password = getpass("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords don't match")
        return
    
    async with SessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ User with email {email} already exists")
            return
        
        # Create admin user
        admin_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role}")
        print(f"   ID: {admin_user.id}")


if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)