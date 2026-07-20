from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from app.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    reminder_time = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)