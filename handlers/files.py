from aiogram import types, F
from database.connection import get_db
from models import File
from utils.auth import require_auth

@require_auth
async def handle_photo(message: types.Message, user, session):
    """Обработка фото"""
    if not message.photo:
        return

    # Получаем самое большое фото
    photo = message.photo[-1]

    # Сохраняем информацию о файле
    file_record = File(
        request_id=None,  # Будет установлено позже в контексте заявки
        file_type="photo",
        file_id=photo.file_id,
        file_name=None
    )

    # Здесь можно добавить логику привязки к заявке
    # Пока просто сохраняем в БД для демонстрации

    session.add(file_record)
    await session.commit()

    await message.reply("📎 Фото получено и сохранено!")

@require_auth
async def handle_document(message: types.Message, user, session):
    """Обработка документов"""
    if not message.document:
        return

    document = message.document

    # Сохраняем информацию о файле
    file_record = File(
        request_id=None,  # Будет установлено позже в контексте заявки
        file_type="document",
        file_id=document.file_id,
        file_name=document.file_name
    )

    session.add(file_record)
    await session.commit()

    await message.reply(f"📎 Документ '{document.file_name}' получен и сохранен!")

def register_file_handlers(dp):
    """Регистрация обработчиков файлов"""
    dp.message.register(handle_photo, F.photo)
    dp.message.register(handle_document, F.document)