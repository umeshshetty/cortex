"""
Cortex - Memory Models
SQLAlchemy models for TimeDB.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class Note(Base):
    """
    Raw chronological note/event.
    """
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String, default="user")  # user, system, email, etc.
    
    # RAG Status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Note {self.id}: {self.content[:20]}...>"
