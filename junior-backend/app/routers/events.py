from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.deps import get_db, get_current_user   # IMPORTANT: fixed import
import dateparser
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=schemas.event.EventOut)
def create_event(
    event: schemas.event.EventCreate,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user)
):
    db_event = models.event.Event(
        user_id=current_user.id,
        title=event.title,
        description=event.description,
        reminder_time=event.reminder_time
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.post("/natural")
def create_event_natural(
    text: str,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user)
):
    logger.info(f"Raw text received: {text}")
    parsed_date = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})
    if not parsed_date:
        raise HTTPException(status_code=400, detail="Could not parse a date/time from your text")
    
    db_event = models.event.Event(
        user_id=current_user.id,
        title=text,
        reminder_time=parsed_date
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/upcoming", response_model=list[schemas.event.EventOut])
def get_upcoming_events(
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user)
):
    events = db.query(models.event.Event).filter(
        models.event.Event.user_id == current_user.id,
        models.event.Event.reminder_time >= datetime.utcnow(),
        models.event.Event.is_completed == False
    ).order_by(models.event.Event.reminder_time.asc()).all()
    return events