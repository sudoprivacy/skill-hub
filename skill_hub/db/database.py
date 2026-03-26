"""Database connection management"""

import logging
from typing import Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker

from skill_hub.config.config import Config

logger = logging.getLogger(__name__)

# Global engine instances
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def init_db(config: Config) -> None:
    """Initialize database connections
    
    Args:
        config: Application configuration
    """
    global _engine, _session_factory
    
    if not config.has_database:
        logger.info("No database configuration provided, skipping database initialization")
        return
    
    try:
        # Ensure database URL uses async driver
        db_url = config.database_url
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://")

        # Create async engine
        _engine = create_async_engine(
            db_url,
            pool_size=config.database_pool_size,
            max_overflow=config.database_max_overflow,
            pool_recycle=config.database_pool_recycle,
            echo=config.debug,
        )
        
        # Create session factory
        _session_factory = async_sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        
        logger.info("Database connections initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database connections: {e}")
        raise


def get_engine() -> AsyncEngine:
    """Get the asynchronous database engine
    
    Returns:
        SQLAlchemy async engine instance
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db() first.")
    return _engine


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get a database session (context manager)
    
    Yields:
        Database session
        
    Example:
        with get_session() as session:
            result = session.query(User).all()
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Close all database connections"""
    global _engine
    
    if _engine:
        await _engine.dispose()
        logger.info("Database connections closed")
    
    logger.info("All database connections closed")
