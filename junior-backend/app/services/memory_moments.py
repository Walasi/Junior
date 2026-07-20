from sqlalchemy.orm import Session
from app.models.important_moment import ImportantMoment
from app.models.user import User
from datetime import datetime, timedelta

def capture_important_moment(db: Session, user_id: int, text: str, sentiment: float = None):
    """Store a positive milestone or achievement."""
    # Heuristic: if user says "I did it", "I achieved", "I won", etc.
    lower = text.lower()
    keywords = ["i did it", "i achieved", "i won", "i got", "i finished", "i completed", "proud", "success"]
    if any(k in lower for k in keywords):
        moment = ImportantMoment(user_id=user_id, text=text, mood_score=sentiment)
        db.add(moment)
        db.commit()
        return True
    return False

def retrieve_uplifting_memory(db: Session, user_id: int) -> str:
    """Get a random recent important moment to lift mood."""
    from sqlalchemy.sql import func
    moment = db.query(ImportantMoment).filter(
        ImportantMoment.user_id == user_id,
        ImportantMoment.created_at > datetime.utcnow() - timedelta(days=365)
    ).order_by(func.random()).first()
    if moment:
        return f"Remember when you {moment.text}? That was a great moment!"
    return "You've had many good moments – let's create more together."