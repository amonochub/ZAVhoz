import logging
from aiogram import F, types

from utils.auth import require_auth
from utils.keyboard import get_back_keyboard

logger = logging.getLogger(__name__)


@require_auth
async def handle_photo(message: types.Message, user, session):
    """Обработка фото вне контекста - направляем пользователя на создание заявки"""
    if not message.photo:
        return

    # Вместо сохранения файла без контекста, направляем пользователя
    await message.reply(
        "📸 <b>Фото получено!</b>\n\n"
        "Чтобы создать заявку с этим фото, используйте меню:\n\n"
        "1️⃣ Нажмите '📝 Создание заявки'\n"
        "2️⃣ Отправьте фото с описанием проблемы\n\n"
        "<i>Фото будет автоматически прикреплено к заявке</i>",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📝 Создать заявку", callback_data="create_request")],
            [types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ]),
        parse_mode="HTML"
    )


@require_auth
async def handle_document(message: types.Message, user, session):
    """Обработка документов вне контекста - направляем пользователя"""
    if not message.document:
        return

    document = message.document

    await message.reply(
        f"📄 <b>Документ '{document.file_name}' получен!</b>\n\n"
        "Чтобы прикрепить документ к заявке, используйте меню:\n\n"
        "1️⃣ Нажмите '📝 Создание заявки'\n"
        "2️⃣ Отправьте документ с описанием\n\n"
        "<i>Документ будет автоматически прикреплен к заявке</i>",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📝 Создать заявку", callback_data="create_request")],
            [types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ]),
        parse_mode="HTML"
    )


def register_file_handlers(dp):
    """Регистрация обработчиков файлов"""
    dp.message.register(handle_photo, F.photo)
    dp.message.register(handle_document, F.document)
