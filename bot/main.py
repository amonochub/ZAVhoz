"""Main bot entry point."""

import asyncio
import os
from typing import NoReturn

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize structured logging
from utils.logging_config import get_logger, init_logging

init_logging()
logger = get_logger(__name__)

# Initialize Sentry for error tracking
from utils.sentry_config import init_sentry

init_sentry()

# Get bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize notification service
from utils.notifications import get_notification_service

notification_service = get_notification_service(bot)

# Import and register handlers
from handlers import (
    register_admin_handlers,
    register_create_request_handlers,
    register_file_handlers,
    register_menu_handlers,
    register_request_actions_handlers,
    register_start_handlers,
)


def register_all_handlers() -> None:
    """Register all message handlers."""
    logger.info("Registering all handlers...", count=6)
    register_start_handlers(dp)
    register_menu_handlers(dp)
    register_create_request_handlers(dp)
    register_admin_handlers(dp)
    register_request_actions_handlers(dp)
    register_file_handlers(dp)
    logger.info("All handlers registered successfully")


async def main() -> NoReturn:
    """Main bot function."""
    try:
        register_all_handlers()

        # Create database tables
        from database.migrations import create_tables
        create_tables()
        logger.info("Database tables created/verified")

        logger.info("Bot startup complete", status="running")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Fatal error during startup", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
