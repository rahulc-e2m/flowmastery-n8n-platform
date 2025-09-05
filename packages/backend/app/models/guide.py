from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.models.base import Base


class Guide(Base):
    """Model for storing platform guide instructions and API setup guides."""
    
    __tablename__ = "guides"  # Changed to avoid table conflicts

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, comment="Display title for the guide")
    platform_name = Column(String(255), nullable=False, unique=True)
    where_to_get = Column(Text, nullable=True, comment="URL where users can get API keys/credentials")
    guide_link = Column(Text, nullable=True, comment="Link to step-by-step guide")
    documentation_link = Column(Text, nullable=True, comment="Link to official documentation")
    description = Column(Text, nullable=True, comment="Brief description of the platform")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Guide(platform_name='{self.platform_name}')>"
