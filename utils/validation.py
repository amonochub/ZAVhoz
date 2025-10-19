"""Validation utilities for request data and rate limiting."""

import logging
import re
import time
from typing import Any, Tuple

logger = logging.getLogger(__name__)


def validate_request_title(title: str) -> Tuple[bool, str]:
    """Validate request title.
    
    Args:
        title: Request title to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "Request title cannot be empty"

    if len(title.strip()) < 3:
        return False, "Request title must contain at least 3 characters"

    if len(title.strip()) > 100:
        return False, "Request title must not exceed 100 characters"

    return True, ""


def validate_request_description(description: str) -> Tuple[bool, str]:
    """Validate request description.
    
    Args:
        description: Request description to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not description or not description.strip():
        return False, "Request description cannot be empty"

    if len(description.strip()) < 10:
        return False, "Request description must contain at least 10 characters"

    if len(description.strip()) > 1000:
        return False, "Request description must not exceed 1000 characters"

    return True, ""


def validate_location(location: str) -> Tuple[bool, str]:
    """Validate location.
    
    Args:
        location: Location to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not location or not location.strip():
        return False, "Location cannot be empty"

    if len(location.strip()) < 3:
        return False, "Location must contain at least 3 characters"

    if len(location.strip()) > 100:
        return False, "Location must not exceed 100 characters"

    return True, ""


def validate_comment(comment: str) -> Tuple[bool, str]:
    """Validate comment.
    
    Args:
        comment: Comment to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not comment or not comment.strip():
        return False, "Comment cannot be empty"

    if len(comment.strip()) > 500:
        return False, "Comment must not exceed 500 characters"

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


class RateLimiter:
    """Simple in-memory rate limiter to protect against spam."""

    def __init__(self) -> None:
        """Initialize rate limiter."""
        self.requests: dict[str, list[float]] = {}

    def is_allowed(
        self,
        user_id: int,
        action: str = "default",
        max_requests: int = 5,
        time_window: int = 60,
    ) -> bool:
        """Check if request is allowed.
        
        Args:
            user_id: User ID
            action: Action name for grouping
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
            
        Returns:
            True if request is allowed, False otherwise
        """
        key = f"{user_id}_{action}"
        current_time = time.time()

        if key not in self.requests:
            self.requests[key] = []

        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if current_time - t < time_window]

        # Check limit
        if len(self.requests[key]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {key}")
            return False

        # Add current request
        self.requests[key].append(current_time)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()