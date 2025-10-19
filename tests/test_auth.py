"""Tests for authentication utilities."""

import pytest
from aiogram import types
from unittest.mock import AsyncMock, MagicMock

from utils.auth import get_or_create_user, is_admin


class TestGetOrCreateUser:
    """Test user creation and retrieval."""

    @pytest.mark.asyncio
    async def test_get_existing_user(self, db_session) -> None:
        """Test retrieving existing user."""
        from models import User

        # Create test user
        user = User(
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            role="user",
        )
        db_session.add(user)
        await db_session.commit()

        # Mock message
        message = AsyncMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"

        # Test
        result = await get_or_create_user(message, db_session)
        assert result.telegram_id == 123456
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_create_new_user(self, db_session) -> None:
        """Test creating new user."""
        # Mock message
        message = AsyncMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 789012
        message.from_user.username = "newuser"
        message.from_user.first_name = "New"
        message.from_user.last_name = "User"

        # Test
        result = await get_or_create_user(message, db_session)
        assert result.telegram_id == 789012
        assert result.username == "newuser"
        assert result.role == "user"
        assert result.is_active is True


class TestIsAdmin:
    """Test admin check."""

    @pytest.mark.asyncio
    async def test_is_admin_true(self, monkeypatch) -> None:
        """Test admin user."""
        monkeypatch.setenv("ADMIN_USER_ID", "123456789")
        # Need to reload module to pick up new env var
        import importlib
        import utils.auth
        importlib.reload(utils.auth)

        result = await utils.auth.is_admin(123456789)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_admin_false(self, monkeypatch) -> None:
        """Test non-admin user."""
        monkeypatch.setenv("ADMIN_USER_ID", "123456789")
        import importlib
        import utils.auth
        importlib.reload(utils.auth)

        result = await utils.auth.is_admin(999999999)
        assert result is False
