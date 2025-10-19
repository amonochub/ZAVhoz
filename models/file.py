from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from .base import Base


class File(Base):
    __tablename__ = "files"

    id: int = Column(Integer, primary_key=True, index=True)
    request_id: int = Column(Integer, ForeignKey("requests.id"), nullable=False)
    file_type: str = Column(String(50), nullable=False)  # photo, document
    file_id: str = Column(String(255), nullable=False)  # Telegram file_id
    file_name: Optional[str] = Column(String(255), nullable=True)
    uploaded_by: Optional[int] = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who uploaded
    uploaded_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
