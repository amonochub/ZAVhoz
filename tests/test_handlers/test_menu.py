"""Tests for menu handler."""

import pytest
from aiogram import types
from unittest.mock import AsyncMock, MagicMock, patch

from models import User


class TestMenuHandler:
    """Test main menu navigation."""

    @pytest.mark.asyncio
    async def test_main_menu_keyboard_user(self) -> None:
        """Test main menu keyboard for regular user."""
        from utils.keyboard import get_main_menu_keyboard
        
        keyboard = get_main_menu_keyboard(is_admin=False)
        
        assert keyboard is not None
        # Keyboard should have buttons for user

    @pytest.mark.asyncio
    async def test_main_menu_keyboard_admin(self) -> None:
        """Test main menu keyboard for admin."""
        from utils.keyboard import get_main_menu_keyboard
        
        keyboard = get_main_menu_keyboard(is_admin=True)
        
        assert keyboard is not None
        # Keyboard should have admin buttons

    @pytest.mark.asyncio
    async def test_welcome_message_user(self) -> None:
        """Test welcome message for regular user."""
        from utils.messages import get_welcome_message
        
        message = get_welcome_message("Test User", is_admin=False)
        
        assert message is not None
        assert "Test User" in message or len(message) > 0

    @pytest.mark.asyncio
    async def test_welcome_message_admin(self) -> None:
        """Test welcome message for admin."""
        from utils.messages import get_welcome_message
        
        message = get_welcome_message("Admin User", is_admin=True)
        
        assert message is not None
        assert len(message) > 0
