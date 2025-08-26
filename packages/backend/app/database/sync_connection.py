from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import get_settings

settings = get_settings()

# Create sync engine for database operations
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", ""),
    pool_pre_ping=True,
    pool_recycle=300,
)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_sync_db():
    """Get synchronous database session"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()