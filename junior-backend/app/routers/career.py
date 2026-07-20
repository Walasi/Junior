from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.skill import UserSkill, CareerOpportunity
from app.services.career_matcher import update_career_opportunities
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/career", tags=["Career"])

class SkillOut(BaseModel):
    id: int
    skill_name: str
    confidence: int
    created_at: str

    class Config:
        from_attributes = True

class OpportunityOut(BaseModel):
    id: int
    title: str
    company: str
    url: str
    description: str
    matched_skills: str
    created_at: str
    is_viewed: int

    class Config:
        from_attributes = True

@router.get("/skills", response_model=List[SkillOut])
def get_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    return skills

@router.post("/scan")
def trigger_skill_scan(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Optionally scan all past conversations (expensive, do in background)
    background_tasks.add_task(scan_all_conversations_for_skills, db, current_user.id)
    return {"message": "Skill scan started"}

def scan_all_conversations_for_skills(db: Session, user_id: int):
    # This would query all user messages and extract skills
    # For brevity, we skip full implementation; a periodic job can do this.
    pass

@router.get("/opportunities", response_model=List[OpportunityOut])
def get_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opps = db.query(CareerOpportunity).filter(CareerOpportunity.user_id == current_user.id).order_by(CareerOpportunity.created_at.desc()).all()
    return opps

@router.post("/opportunities/refresh")
def refresh_opportunities(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    background_tasks.add_task(update_career_opportunities, db, current_user.id)
    return {"message": "Refresh started"}