from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from .base import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    file_type = Column(String(50), nullable=False)  # photo, document
    file_id = Column(String(255), nullable=False)  # Telegram file_id
    file_name = Column(String(255), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who uploaded
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
