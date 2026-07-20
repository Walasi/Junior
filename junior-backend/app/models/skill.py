from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    source_message = Column(Text, nullable=True)   # which conversation it came from
    confidence = Column(Integer, default=80)       # 0-100 placeholder
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CareerOpportunity(Base):
    __tablename__ = "career_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    matched_skills = Column(Text, nullable=True)   # JSON list as string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_viewed = Column(Integer, default=0)