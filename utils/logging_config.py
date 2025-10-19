"""Structured logging configuration with structlog."""

import logging
import logging.handlers
import os
import sys
from datetime import datetime

import structlog
from dotenv import load_dotenv

load_dotenv()

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else "logs", exist_ok=True)


def add_log_level(logger, method_name, event_dict):
    """Add log level to event dict."""
    if "level" not in event_dict:
        event_dict["level"] = method_name.upper()
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """Add timestamp to event dict."""
    if "timestamp" not in event_dict:
        event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def configure_structlog() -> None:
    """Configure structlog for structured logging."""
    # Timestamper
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    # Shared processors
    shared_processors = [
        add_log_level,
        add_timestamp,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if LOG_FORMAT == "json":
        # JSON format
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Text format
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def setup_file_logging() -> None:
    """Setup file-based logging with rotation."""
    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
    )

    # Set formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    # Get root logger and add handler
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(getattr(logging, LOG_LEVEL))


def setup_console_logging() -> None:
    """Setup console logging."""
    console_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, LOG_LEVEL))


class BotContextLogger:
    """Context manager for tracking bot operations."""

    def __init__(self, operation: str, user_id: int = None, **context):
        """Initialize context logger."""
        self.operation = operation
        self.user_id = user_id
        self.context = context
        self.logger = get_logger(__name__)

    def __enter__(self):
        """Enter context."""
        self.logger.info(
            "operation_start",
            operation=self.operation,
            user_id=self.user_id,
            **self.context,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type:
            self.logger.error(
                "operation_error",
                operation=self.operation,
                user_id=self.user_id,
                error=str(exc_val),
                error_type=exc_type.__name__,
                **self.context,
            )
            return False

        self.logger.info(
            "operation_complete",
            operation=self.operation,
            user_id=self.user_id,
            **self.context,
        )
        return True


def init_logging() -> None:
    """Initialize all logging systems."""
    configure_structlog()
    setup_console_logging()
    setup_file_logging()
    logger = get_logger(__name__)
    logger.info("logging_initialized", level=LOG_LEVEL, format=LOG_FORMAT)
