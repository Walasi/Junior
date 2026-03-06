from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)  # optional at signup
    voice_print = Column(String, nullable=True)  # placeholder for voice embedding
    created_at = Column(DateTime(timezone=True), server_default=func.now())