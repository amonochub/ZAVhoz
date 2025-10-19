"""Sentry error tracking configuration."""

import os
from typing import Optional

import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.logging import LoggingIntegration

load_dotenv()

# Sentry Configuration
SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
SENTRY_ENABLED: bool = os.getenv("SENTRY_ENABLED", "false").lower() == "true"
SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))


def init_sentry() -> None:
    """Initialize Sentry for error tracking and performance monitoring."""
    if not SENTRY_ENABLED or not SENTRY_DSN:
        return

    # Create logging integration
    logging_integration = LoggingIntegration(
        level=20,  # Capture INFO and above as breadcrumbs
        event_level=40,  # Send ERROR and above as events
    )

    # Initialize Sentry
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[logging_integration],
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        # Set to 0.0 to disable performance monitoring
        profiles_sample_rate=0.1,
        # Capture 10% of transactions for profiling
        before_send=before_send_handler,
        debug=False,
    )


def before_send_handler(event: dict, hint: dict) -> Optional[dict]:
    """Filter and process events before sending to Sentry."""
    # Don't send events for specific exceptions
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        
        # Ignore specific exceptions
        if exc_type in [KeyboardInterrupt, SystemExit]:
            return None

    return event


def capture_exception(exception: Exception, context: dict = None) -> None:
    """Capture an exception with optional context."""
    if not SENTRY_ENABLED:
        return

    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", context: dict = None) -> None:
    """Capture a message with optional context."""
    if not SENTRY_ENABLED:
        return

    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: int, username: str = None, **kwargs) -> None:
    """Set user context for error tracking."""
    if not SENTRY_ENABLED:
        return

    sentry_sdk.set_user({
        "id": user_id,
        "username": username,
        **kwargs,
    })


def clear_user_context() -> None:
    """Clear user context."""
    if not SENTRY_ENABLED:
        return

    sentry_sdk.set_user(None)


def set_tag(key: str, value: str) -> None:
    """Set a tag for error tracking."""
    if not SENTRY_ENABLED:
        return

    sentry_sdk.set_tag(key, value)


def set_context(name: str, data: dict) -> None:
    """Set custom context for error tracking."""
    if not SENTRY_ENABLED:
        return

    sentry_sdk.set_context(name, data)
