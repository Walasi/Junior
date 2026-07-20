from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.services.energy_aggregator import get_energy_level
from app.routers.energy import get_yearly_report   # careful about circular import; we can duplicate logic

def send_birthday_wishes():
    db = SessionLocal()
    today = datetime.today().date()
    users = db.query(User).filter(User.date_of_birth.isnot(None)).all()
    for user in users:
        if user.date_of_birth.date() == today:
            # Get yearly report logic (reuse or call internal)
            from app.routers.energy import get_yearly_report_data   # we'll refactor
            report = get_yearly_report_data(db, user.id)   # hypothetical function
            message = f"🎂 Happy Birthday, {user.username}! Here's your yearly report:\n\n"
            message += f"Average energy: {report['energy_level']} ({report['average_sentiment']})\n"
            message += f"Total messages: {report['total_messages']}\n"
            message += f"Wins: {report['wins_count']}, Losses: {report['losses_count']}\n"
            message += f"Recommendation: {report['recommendations'][0] if report['recommendations'] else 'Keep going!'}"
            # Store as system conversation
            conv = Conversation(
                user_id=user.id,
                message="[System] Birthday Report",
                response=message,
                topic="birthday"
            )
            db.add(conv)
    db.commit()
    db.close()