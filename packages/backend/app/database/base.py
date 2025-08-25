"""Database base imports"""

from app.models.base import Base

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.client import Client  
from app.models.invitation import Invitation

__all__ = ["Base"]