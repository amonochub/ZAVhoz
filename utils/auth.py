"""Authentication and authorization utilities."""

import logging
import os
from typing import Callable, Any, TypeVar

from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps

from database.connection import get_db
from models import User

logger = logging.getLogger(__name__)

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))

T = TypeVar("T", bound=Callable[..., Any])


async def get_or_create_user(message: types.Message, session: AsyncSession) -> User:
    """Get or create user from Telegram message.
    
    Args:
        message: Aiogram message object
        session: SQLAlchemy async session
        
    Returns:
        User model instance
    """
    telegram_id = message.from_user.id

    # Check if user exists
    stmt = select(User).where(User.telegram_id == telegram_id)
    user = await session.scalar(stmt)
    
    if user:
        return user

    # Create new user
    user = User(
        telegram_id=telegram_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        role="admin" if telegram_id == ADMIN_USER_ID else "user",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def is_admin(user_id: int) -> bool:
    """Check if user is administrator.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if user is admin, False otherwise
    """
    return user_id == ADMIN_USER_ID


def require_auth(func: T) -> T:
    """Decorator to require user authentication.
    
    Automatically gets or creates user and passes it to handler.
    Works with both Message and CallbackQuery.
    
    Args:
        func: Handler function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(update: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            # Extract message and from_user based on update type
            if isinstance(update, types.CallbackQuery):
                message = update.message
                from_user = update.from_user
            else:  # types.Message
                message = update
                from_user = update.from_user
            
            # Get database session
            async for session in get_db():
                try:
                    # Get or create user
                    user = await get_or_create_user(message, session)
                    
                    if not user.is_active:
                        if isinstance(update, types.CallbackQuery):
                            await update.answer("Your account has been disabled.", show_alert=True)
                        else:
                            await message.reply("Your account has been disabled.")
                        return
                    
                    # Call handler with proper arguments
                    return await func(update, *args, user=user, session=session, **kwargs)
                except Exception as e:
                    logger.error(f"Auth error for user {from_user.id}: {e}", exc_info=True)
                    # Notify user of error appropriately
                    try:
                        if isinstance(update, types.CallbackQuery):
                            await update.answer("An error occurred. Please try again later.", show_alert=True)
                        else:
                            await message.reply("An error occurred. Please try again later.")
                    except:
                        pass  # Silently ignore notification errors
                    raise
        except Exception as e:
            logger.error(f"Unexpected error in require_auth: {e}", exc_info=True)
            raise
    
    return wrapper  # type: ignore


def require_admin(func: T) -> T:
    """Decorator to require admin privileges.
    
    Args:
        func: Handler function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(message: types.Message, *args: Any, **kwargs: Any) -> Any:
        if not await is_admin(message.from_user.id):
            await message.reply("You don't have permission to execute this command.")
            return
        
        return await func(message, *args, **kwargs)
    
    return wrapper  # type: ignore