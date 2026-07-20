from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import JSON

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=True) 
    voice_print = Column(JSON, nullable=True)  # store as JSON list
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    emotions = relationship("UserEmotion", back_populates="user", cascade="all, delete-orphan")
    life_events = relationship("LifeEvent", back_populates="user", cascade="all, delete-orphan")
    onboarding_step = Column(Integer, default=0) 
    why_game_state = Column(JSON, nullable=True, default=None)
    profile_data = Column(JSON, nullable=True, default={})