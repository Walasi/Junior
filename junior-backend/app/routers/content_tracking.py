from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import User, ContentItem
from app.deps import get_current_user

router = APIRouter(prefix="/content", tags=["content tracking"])

# Schemas
class ContentCreate(BaseModel):
    title: str
    content_type: str  # article, video, podcast, book
    url: Optional[str] = None
    notes: Optional[str] = None
    status: str = "planned"  # planned, in_progress, completed

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ContentResponse(BaseModel):
    id: int
    title: str
    content_type: str
    url: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: int

    class Config:
        from_attributes = True

# CRUD Endpoints
@router.post("/", response_model=ContentResponse)
def create_content(
    item: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_item = ContentItem(
        **item.dict(),
        user_id=current_user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[ContentResponse])
def list_content(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ContentItem).filter(ContentItem.user_id == current_user.id)
    if status:
        query = query.filter(ContentItem.status == status)
    return query.all()

@router.get("/{item_id}", response_model=ContentResponse)
def get_content(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ContentItem).filter(
        ContentItem.id == item_id,
        ContentItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return item

@router.put("/{item_id}", response_model=ContentResponse)
def update_content(
    item_id: int,
    update: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ContentItem).filter(
        ContentItem.id == item_id,
        ContentItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    for key, value in update.dict(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_content(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ContentItem).filter(
        ContentItem.id == item_id,
        ContentItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    db.delete(item)
    db.commit()
    return {"message": "Content deleted"}