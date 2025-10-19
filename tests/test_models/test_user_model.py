"""Tests for User model."""

import pytest
from sqlalchemy import select

from models import User


class TestUserModel:
    """Test User model creation and properties."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: any) -> None:
        """Test creating a user."""
        user = User(
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            role="user",
        )
        db_session.add(user)
        await db_session.commit()

        # Retrieve and verify
        stmt = select(User).where(User.telegram_id == 123456)
        retrieved = await db_session.scalar(stmt)

        assert retrieved is not None
        assert retrieved.username == "testuser"
        assert retrieved.first_name == "Test"
        assert retrieved.last_name == "User"
        assert retrieved.role == "user"
        assert retrieved.is_active is True

    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session: any) -> None:
        """Test user model default values."""
        user = User(
            telegram_id=999,
            username="default_test",
        )
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.telegram_id == 999)
        retrieved = await db_session.scalar(stmt)

        assert retrieved.role == "user"
        assert retrieved.is_active is True
        assert retrieved.created_at is not None

    @pytest.mark.asyncio
    async def test_user_admin_role(self, db_session: any) -> None:
        """Test creating admin user."""
        admin = User(
            telegram_id=111,
            username="admin",
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()

        stmt = select(User).where(User.telegram_id == 111)
        retrieved = await db_session.scalar(stmt)

        assert retrieved.role == "admin"

    @pytest.mark.asyncio
    async def test_user_deactivation(self, db_session: any) -> None:
        """Test deactivating user."""
        user = User(telegram_id=222, username="deactive")
        db_session.add(user)
        await db_session.commit()

        # Deactivate
        user.is_active = False
        await db_session.commit()

        # Verify
        stmt = select(User).where(User.telegram_id == 222)
        retrieved = await db_session.scalar(stmt)
        assert retrieved.is_active is False
