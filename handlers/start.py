from aiogram import types
from aiogram.filters import Command
from utils.auth import get_or_create_user, is_admin
from utils.keyboard import get_main_menu_keyboard
from utils.messages import get_welcome_message
from database.connection import get_db

async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    async for session in get_db():
        user = await get_or_create_user(message, session)
        is_admin_user = await is_admin(user.telegram_id)

        welcome_text = get_welcome_message(
            user.first_name or user.username or "пользователь",
            is_admin_user
        )

        keyboard = get_main_menu_keyboard(is_admin_user)
        await message.reply(welcome_text, reply_markup=keyboard, parse_mode="HTML")

def register_start_handlers(dp):
    """Регистрация обработчиков"""
    dp.message.register(start_handler, Command("start"))