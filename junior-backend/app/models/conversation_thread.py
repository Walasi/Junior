from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class ConversationThread(Base):
    __tablename__ = "conversation_threads"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)  # auto-generated from first message
    created_at = Column(DateTime(timezone=True), server_default=func.now())