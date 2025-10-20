import logging
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

# Configure timeouts based on database type
connect_args = {}
if "postgresql" in DATABASE_URL:
    # PostgreSQL supports both timeout and command_timeout
    connect_args = {
        "timeout": 10,  # Connection timeout: 10 seconds
        "command_timeout": 30,  # Command timeout: 30 seconds
    }
else:
    # SQLite only supports timeout
    connect_args = {
        "timeout": 10,  # Connection timeout: 10 seconds
    }

# Create async engine with proper configuration
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,  # Disable query logging for security
    future=True,
    connect_args=connect_args
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager."""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
