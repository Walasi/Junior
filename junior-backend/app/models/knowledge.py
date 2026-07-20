from sqlalchemy import Column, Integer, String, Text, JSON
from app.database import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    topics = Column(JSON, nullable=True, default=list)
    embedding = Column(JSON, nullable=True)