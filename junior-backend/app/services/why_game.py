from sqlalchemy.orm import Session
from app.models.user import User

def start_why_game(db: Session, user: User, goal: str):
    """Initialize why game for a user."""
    user.why_game_state = {
        "active": True,
        "goal": goal,
        "question_count": 0
    }
    db.commit()
    return "Why do you want to achieve that? (I'll ask 'why?' up to 7 times to help you clarify.)"

def continue_why_game(db: Session, user: User, answer: str) -> tuple[str, bool]:
    """Process user answer and return next question or completion."""
    state = user.why_game_state
    if not state or not state.get("active"):
        return "", False
    
    state["question_count"] += 1
    if state["question_count"] >= 7:
        # Game ends
        user.why_game_state = None
        db.commit()
        return f"Thanks for exploring! Your core motivation for '{state['goal']}' seems to be: {answer}. Keep that in mind.", True
    else:
        next_q = f"Why is that important to you? (Question {state['question_count']+1}/7)"
        db.commit()
        return next_q, True