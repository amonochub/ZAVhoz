"""Validation utilities for request data and rate limiting."""

import logging
import re
from typing import Tuple, Optional

from utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


def validate_request_title(title: str) -> Tuple[bool, str]:
    """Validate request title.

    Args:
        title: Request title to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "🏷️ Название заявки не может быть пустым. Введите название проблемы, например: 'Нет туалетной бумаги'"

    if len(title.strip()) < 3:
        return False, "🏷️ Название слишком короткое. Минимум 3 символа"

    if len(title.strip()) > 100:
        return False, "🏷️ Название слишком длинное. Максимум 100 символов"

    return True, ""


def validate_request_description(description: str) -> Tuple[bool, str]:
    """Validate request description.

    Args:
        description: Request description to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not description or not description.strip():
        return False, "📝 Описание не может быть пустым. Опишите проблему подробнее, минимум 10 символов"

    if len(description.strip()) < 10:
        return False, "📝 Описание слишком короткое. Минимум 10 символов"

    if len(description.strip()) > 1000:
        return False, "📝 Описание слишком длинное. Максимум 1000 символов"

    return True, ""


def validate_location(location: str) -> Tuple[bool, str]:
    """Validate location.

    Args:
        location: Location to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not location or not location.strip():
        return False, "📍 Местоположение не может быть пустым. Укажите кабинет или этаж, например: 'Кабинет 101'"

    if len(location.strip()) < 3:
        return False, "📍 Местоположение слишком короткое. Минимум 3 символа"

    if len(location.strip()) > 100:
        return False, "📍 Местоположение слишком длинное. Максимум 100 символов"

    return True, ""


def validate_comment(comment: str) -> Tuple[bool, str]:
    """Validate comment.

    Args:
        comment: Comment to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not comment or not comment.strip():
        return False, "💬 Комментарий не может быть пустым"

    if len(comment.strip()) > 500:
        return False, "💬 Комментарий слишком длинный. Максимум 500 символов"

    return True, ""


def sanitize_text(text: str) -> str:
    """Sanitize text by removing dangerous characters and limiting length.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove extra whitespace and line breaks
    text = re.sub(r"\s+", " ", text.strip())

    # Limit length
    if len(text) > 10000:
        text = text[:10000] + "..."

    return text


def validate_file(file_type: str, file_size: Optional[int] = None) -> Tuple[bool, str]:
    """Validate uploaded file type and size.
    
    Args:
        file_type: File type ('photo' or 'document')
        file_size: File size in bytes (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    allowed_types = ['photo', 'document']
    
    if file_type not in allowed_types:
        return False, f"❌ Тип файла не поддерживается. Разрешены: {', '.join(allowed_types)}"
    
    # Проверяем размер (Telegram обычно ограничивает 20MB)
    if file_size and file_size > 20 * 1024 * 1024:  # 20MB
        return False, "❌ Файл слишком большой. Максимум 20 МБ"
    
    return True, ""


def validate_image_caption(caption: Optional[str]) -> Tuple[bool, str]:
    """Validate photo caption (description of problem).
    
    Args:
        caption: Photo caption/description
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not caption or not caption.strip():
        return False, "📝 Для фото обязательно нужно описание проблемы (минимум 3 символа)"
    
    # Используем существующую валидацию для названия
    return validate_request_title(caption)
