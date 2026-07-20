from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.conversation import Conversation
from app.models.daily_energy import DailyEnergy

def get_energy_level(avg_sentiment: float) -> str:
    if avg_sentiment <= -0.5: return "Very Low"
    elif avg_sentiment < -0.1: return "Low"
    elif avg_sentiment < 0.3: return "Moderate"
    elif avg_sentiment < 0.7: return "Good"
    else: return "High"

def aggregate_daily_energy(db: Session, target_date: datetime = None):
    """
    Compute daily sentiment aggregates for all users for a given date (default: yesterday).
    """
    if target_date is None:
        target_date = datetime.utcnow().date() - timedelta(days=1)
    else:
        target_date = target_date.date()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())

    # Get all users who had conversations on that day
    results = db.query(
        Conversation.user_id,
        func.avg(Conversation.sentiment_score).label('avg_sentiment'),
        func.count(Conversation.id).label('msg_count')
    ).filter(
        Conversation.timestamp >= start,
        Conversation.timestamp <= end,
        Conversation.sentiment_score.isnot(None)
    ).group_by(Conversation.user_id).all()

    for user_id, avg_sent, msg_count in results:
        energy_level = get_energy_level(avg_sent) if avg_sent is not None else None
        # Upsert
        existing = db.query(DailyEnergy).filter(
            DailyEnergy.user_id == user_id,
            DailyEnergy.date == target_date
        ).first()
        if existing:
            existing.avg_sentiment = avg_sent
            existing.message_count = msg_count
            existing.energy_level = energy_level
        else:
            daily = DailyEnergy(
                user_id=user_id,
                date=target_date,
                avg_sentiment=avg_sent,
                message_count=msg_count,
                energy_level=energy_level
            )
            db.add(daily)
    db.commit()