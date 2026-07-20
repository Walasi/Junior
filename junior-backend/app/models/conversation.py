from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    sentiment_score = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    topic = Column(String, nullable=True)  
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    emotions = relationship("UserEmotion", back_populates="conversation", cascade="all, delete-orphan")
    thread_id = Column(Integer, ForeignKey("conversation_threads.id"), nullable=True)