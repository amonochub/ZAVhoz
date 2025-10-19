import asyncio
import logging
import os
from typing import NoReturn

from sqlalchemy import create_engine
from dotenv import load_dotenv

from models import Base

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)


def create_tables() -> None:
    """Create all database tables from models."""
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        engine.dispose()
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


if __name__ == "__main__":
    create_tables()