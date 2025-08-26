from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
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

@contextmanager
def get_sync_db_session():
    """Get synchronous database session as context manager for Celery tasks"""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()