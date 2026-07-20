from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db
from app.models.knowledge import KnowledgeBase
from app.services.knowledge import generate_embedding, search_knowledge
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

class KnowledgeItemCreate(BaseModel):
    question: str
    answer: str
    topics: List[str] = []

class KnowledgeItemOut(KnowledgeItemCreate):
    id: int

@router.post("/items", response_model=KnowledgeItemOut)
def create_knowledge_item(item: KnowledgeItemCreate, db: Session = Depends(get_db)):
    embedding = generate_embedding(item.question + " " + item.answer)
    db_item = KnowledgeBase(
        question=item.question,
        answer=item.answer,
        topics=item.topics,
        embedding=embedding
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
