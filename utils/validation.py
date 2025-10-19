"""Validation utilities for request data and rate limiting."""

import logging
import re
from typing import Tuple

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
