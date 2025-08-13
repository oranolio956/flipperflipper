import os
import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event, pool
import asyncpg

from .circuit_breaker import circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://proxyuser:proxypass@localhost:5432/proxydb')
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '40'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

# Create base class for models
Base = declarative_base()

# Configure circuit breaker for database operations
db_circuit_breaker = circuit_breaker.__class__(
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30,
        expected_exception=(asyncpg.PostgresError, Exception),
        success_threshold=2
    )
)


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize database connection with circuit breaker protection"""
        async with self._lock:
            if self._initialized:
                return

            try:
                # Create async engine
                self.engine = create_async_engine(
                    DATABASE_URL,
                    echo=False,
                    pool_size=POOL_SIZE,
                    max_overflow=MAX_OVERFLOW,
                    pool_timeout=POOL_TIMEOUT,
                    pool_recycle=POOL_RECYCLE,
                    pool_pre_ping=True,
                    connect_args={
                        "server_settings": {
                            "application_name": "worker",
                            "jit": "off"
                        },
                        "command_timeout": 60,
                        "timeout": 30,
                    }
                )

                # Create session factory
                self.async_session_maker = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )

                # Test connection
                async with self.engine.begin() as conn:
                    await conn.execute("SELECT 1")

                self._initialized = True
                logger.info("Database connection initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise

    async def close(self):
        """Close database connections"""
        async with self._lock:
            if self.engine:
                await self.engine.dispose()
                self._initialized = False
                logger.info("Database connections closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with circuit breaker protection"""
        if not self._initialized:
            await self.initialize()

        @db_circuit_breaker
        async def _get_session():
            async with self.async_session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        async for session in _get_session():
            yield session


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session"""
    async with db_manager.get_session() as session:
        yield session


# Health check function
async def check_database_health() -> dict:
    """Check database health status"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute("SELECT 1")
            result.scalar()
        return {
            "status": "healthy",
            "circuit_breaker": "closed" if db_circuit_breaker.is_closed() else "open"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "circuit_breaker": "open" if db_circuit_breaker.is_open() else "closed"
        }