from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta, date
from typing import Optional
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from pydantic import BaseModel
from collections import defaultdict
import logging

router = APIRouter(prefix="/energy", tags=["Energy"])
logger = logging.getLogger(__name__)

class EnergyReportResponse(BaseModel):
    period: str = Query("week", pattern="^(day|week|month|year)$")
    start_date: str
    end_date: str
    average_sentiment: float
    energy_level: str  # "Low", "Moderate", "Good", "High"
    trend: str         # "improving", "declining", "stable"
    message_count: int
    recommendations: list[str]

def get_energy_level(sentiment: float) -> str:
    if sentiment <= -0.5:
        return "Very Low"
    elif sentiment < -0.1:
        return "Low"
    elif sentiment < 0.3:
        return "Moderate"
    elif sentiment < 0.7:
        return "Good"
    else:
        return "High"

def get_recommendations(energy_level: str, trend: str) -> list[str]:
    recs = []
    if energy_level in ["Very Low", "Low"]:
        recs.append("It might help to talk about what's bothering you. I'm here to listen.")
        recs.append("Consider taking a break or doing something you enjoy.")
        if trend == "declining":
            recs.append("Your energy has been dropping. Let's find small steps to lift your mood.")
    elif energy_level == "Moderate":
        recs.append("You're doing okay. Maybe try a new activity or reach out to a friend.")
    elif energy_level in ["Good", "High"]:
        recs.append("You're in a great space! Keep up the positive habits.")
    if trend == "improving":
        recs.append("Things are looking up! What's been helping you?")
    elif trend == "declining" and energy_level not in ["Very Low", "Low"]:
        recs.append("Your energy has dipped lately. Want to explore why?")
    return recs

def compute_trend(prev_avg: float, current_avg: float) -> str:
    if current_avg > prev_avg + 0.05:
        return "improving"
    elif current_avg < prev_avg - 0.05:
        return "declining"
    else:
        return "stable"

@router.get("/report", response_model=EnergyReportResponse)
def get_energy_report(
    period: str = Query("week", pattern="^(day|week|month|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an energy report for the user over the specified period.
    Period can be 'day', 'week', 'month', or 'year'.
    """
    now = datetime.utcnow()
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(days=7)
        end_date = now
    elif period == "month":
        start_date = now - timedelta(days=30)
        end_date = now
    else:  # year
        start_date = now - timedelta(days=365)
        end_date = now

    # Query conversations in period
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.timestamp >= start_date,
        Conversation.timestamp <= end_date,
        Conversation.sentiment_score.isnot(None)
    ).order_by(Conversation.timestamp).all()

    if not conversations:
        raise HTTPException(status_code=404, detail="No sentiment data for this period")

    # Compute average sentiment
    avg_sentiment = sum(c.sentiment_score for c in conversations) / len(conversations)
    energy_level = get_energy_level(avg_sentiment)

    # For trend, compare with previous period of same length
    prev_end = start_date
    prev_start = start_date - (end_date - start_date)
    prev_conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.timestamp >= prev_start,
        Conversation.timestamp < prev_end,
        Conversation.sentiment_score.isnot(None)
    ).all()
    if prev_conversations:
        prev_avg = sum(c.sentiment_score for c in prev_conversations) / len(prev_conversations)
        trend = compute_trend(prev_avg, avg_sentiment)
    else:
        trend = "stable"

    recommendations = get_recommendations(energy_level, trend)

    return EnergyReportResponse(
        period=period,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        average_sentiment=round(avg_sentiment, 3),
        energy_level=energy_level,
        trend=trend,
        message_count=len(conversations),
        recommendations=recommendations
    )
    
def get_aggregated_report(db, user_id, start_date, end_date):
    daily_records = db.query(DailyEnergy).filter(
        DailyEnergy.user_id == user_id,
        DailyEnergy.date >= start_date.date(),
        DailyEnergy.date <= end_date.date(),
        DailyEnergy.avg_sentiment.isnot(None)
    ).all()
    if not daily_records:
        return None
    total_messages = sum(r.message_count for r in daily_records)
    avg_sentiment = sum(r.avg_sentiment for r in daily_records) / len(daily_records)
    return avg_sentiment, total_messages

@router.get("/yearly")
def get_yearly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive yearly report based on user's birthday.
    To be called on birthday or manually.
    """
    today = datetime.utcnow().date()
    one_year_ago = today - timedelta(days=365)

    # Conversations in last year
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.timestamp >= one_year_ago,
        Conversation.sentiment_score.isnot(None)
    ).all()
    
    # Life events (wins/losses)
    life_events = db.query(models.life_event.LifeEvent).filter(
        models.life_event.LifeEvent.user_id == current_user.id,
        models.life_event.LifeEvent.created_at >= one_year_ago
    ).all()
    
    wins = [e for e in life_events if e.event_type == 'win']
    losses = [e for e in life_events if e.event_type == 'loss']

    # Aggregate daily energy from DailyEnergy table
    daily = db.query(DailyEnergy).filter(
        DailyEnergy.user_id == current_user.id,
        DailyEnergy.date >= one_year_ago,
        DailyEnergy.avg_sentiment.isnot(None)
    ).order_by(DailyEnergy.date).all()
    
    avg_sentiment = sum(d.avg_sentiment for d in daily) / len(daily) if daily else 0
    total_messages = len(conversations)
    
    # Trend: compare first half vs second half
    mid = len(daily)//2
    if mid >= 2:
        first_half = sum(d.avg_sentiment for d in daily[:mid])/mid
        second_half = sum(d.avg_sentiment for d in daily[mid:])/(len(daily)-mid)
        trend = "improving" if second_half > first_half else "declining" if second_half < first_half else "stable"
    else:
        trend = "stable"
    
    recommendations = []
    if avg_sentiment < 0.2:
        recommendations.append("This year's energy was low. Consider setting small daily goals or talking to a coach.")
    if wins:
        recommendations.append(f"You celebrated {len(wins)} wins! Keep acknowledging achievements.")
    if losses:
        recommendations.append(f"You recorded {len(losses)} losses. It's okay – each is a lesson.")
    
    report = {
        "period": f"{one_year_ago.date()} to {today}",
        "average_sentiment": round(avg_sentiment, 3),
        "energy_level": get_energy_level(avg_sentiment),
        "trend": trend,
        "total_messages": total_messages,
        "wins_count": len(wins),
        "losses_count": len(losses),
        "recommendations": recommendations,
        "daily_data": [{"date": d.date.isoformat(), "energy": d.energy_level} for d in daily[-30:]]  # last 30 days
    }
    return report