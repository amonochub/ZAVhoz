"""Tests for start handler."""

import pytest
from aiogram import types
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from models import User


class TestStartHandler:
    """Test /start command handler."""

    @pytest.mark.asyncio
    async def test_start_creates_new_user(self, db_session: any) -> None:
        """Test /start creates new user in database."""
        # Create mock message
        message = AsyncMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 999999999  # Different from default ADMIN_USER_ID
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        
        # Mock reply method
        message.reply = AsyncMock()
        
        # Import and call handler
        from handlers.start import start_handler
        
        with patch('handlers.start.get_db') as mock_get_db:
            async def mock_session():
                yield db_session
            mock_get_db.return_value = mock_session()
            
            # Call handler
            await start_handler(message)
            
            # Verify user was created
            stmt = select(User).where(User.telegram_id == 999999999)
            user = await db_session.scalar(stmt)
            
            assert user is not None
            assert user.username == "testuser"
            assert user.first_name == "Test"
            assert user.role == "user"
            assert user.is_active is True

    @pytest.mark.asyncio
    async def test_start_existing_user_not_duplicated(self, db_session: any) -> None:
        """Test /start doesn't create duplicate users."""
        # Create existing user
        user1 = User(
            telegram_id=555555555,
            username="existing",
            first_name="Existing",
            role="user",
        )
        db_session.add(user1)
        await db_session.commit()
        
        # Call start handler
        message = AsyncMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 555555555
        message.from_user.username = "existing"
        message.from_user.first_name = "Existing"
        message.reply = AsyncMock()
        
        from handlers.start import start_handler
        
        with patch('handlers.start.get_db') as mock_get_db:
            async def mock_session():
                yield db_session
            mock_get_db.return_value = mock_session()
            
            await start_handler(message)
            
            # Verify only one user exists
            stmt = select(User).where(User.telegram_id == 555555555)
            users = (await db_session.execute(stmt)).scalars().all()
            assert len(users) == 1

    @pytest.mark.asyncio
    async def test_start_with_missing_first_name(self, db_session: any) -> None:
        """Test /start handles missing first_name gracefully."""
        message = AsyncMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 777777777
        message.from_user.username = "noname"
        message.from_user.first_name = None
        message.from_user.last_name = None
        message.reply = AsyncMock()
        
        from handlers.start import start_handler
        
        with patch('handlers.start.get_db') as mock_get_db:
            async def mock_session():
                yield db_session
            mock_get_db.return_value = mock_session()
            
            await start_handler(message)
            
            # Should still create user
            stmt = select(User).where(User.telegram_id == 777777777)
            user = await db_session.scalar(stmt)
            assert user is not None
            assert user.username == "noname"
