import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Priority(enum.Enum):
    HIGH = "высокий"
    MEDIUM = "средний"
    LOW = "низкий"

class Status(enum.Enum):
    OPEN = "открыта"
    IN_PROGRESS = "в работе"
    COMPLETED = "выполнена"
    REJECTED = "отклонена"

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    location = Column(String(100), nullable=False)
    status = Column(SQLEnum(Status), default=Status.OPEN, nullable=False)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    history = Column(JSON, default=list, nullable=False)  # История всех изменений

    user = relationship("User", foreign_keys=[user_id], backref="requests")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    comments = relationship("Comment", backref="request", cascade="all, delete-orphan")
    files = relationship("File", backref="request", cascade="all, delete-orphan")

    def add_history_entry(self, action: str, details: str = "", user_id: int = None) -> None:
        """Добавить запись в историю"""
        if not self.history:
            self.history = []
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "user_id": user_id,
        }
        self.history.append(entry)