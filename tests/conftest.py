"""Pytest configuration and fixtures."""

import os
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models import Base


@pytest.fixture(scope="session")
def database_url() -> str:
    """Get test database URL - using SQLite for tests."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_engine(database_url: str):
    """Create async database engine for tests."""
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get database session for tests."""
    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
        await session.rollback()
