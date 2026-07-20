from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_current_user, get_db
from app.models.user import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/user", tags=["user"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format
    sex: Optional[str] = None
    career_path: Optional[str] = None
    likes: Optional[str] = None
    dislikes: Optional[str] = None
    interests: Optional[str] = None

@router.put("/profile")
def update_profile(profile: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Update profile_data JSON
    if not current_user.profile_data:
        current_user.profile_data = {}
    data = current_user.profile_data
    for key, value in profile.dict(exclude_unset=True).items():
        if value is not None:
            data[key] = value
    current_user.profile_data = data
    db.commit()
    return {"message": "Profile updated", "profile": current_user.profile_data}

@router.get("/profile")
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return current_user.profile_data or {}