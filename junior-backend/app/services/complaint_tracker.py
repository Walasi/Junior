from sqlalchemy.orm import Session
from app.models.user import User
from collections import defaultdict
import re

# In-memory complaint counts per user (or store in DB)
complaint_counts = defaultdict(int)
complaint_topics = defaultdict(lambda: defaultdict(int))  # user_id -> {topic: count}

COMPLAINT_KEYWORDS = [
    "always", "never", "why me", "unfair", "hate", "terrible", "awful",
    "sick of", "tired of", "fed up", "no one", "everyone", "useless", "stupid"
]

def is_complaint(message: str) -> bool:
    lower = message.lower()
    return any(kw in lower for kw in COMPLAINT_KEYWORDS) and len(message.split()) > 3

def extract_topic(message: str) -> str:
    # Simple topic extraction: first noun-like phrase after complaint keywords
    # For now, use generic categories
    lower = message.lower()
    if "work" in lower or "job" in lower or "boss" in lower:
        return "work"
    elif "relationship" in lower or "girlfriend" in lower or "boyfriend" in lower or "partner" in lower:
        return "relationship"
    elif "money" in lower or "bills" in lower or "finance" in lower:
        return "money"
    elif "health" in lower or "sick" in lower:
        return "health"
    else:
        return "general"

def track_complaint(user_id: int, message: str) -> tuple[bool, str]:
    """Returns (should_redirect, redirect_message) if complaint threshold exceeded."""
    if not is_complaint(message):
        return False, ""
    
    topic = extract_topic(message)
    complaint_topics[user_id][topic] += 1
    complaint_counts[user_id] += 1
    
    # If same topic complained >3 times, redirect
    if complaint_topics[user_id][topic] >= 3:
        # Reset count for that topic
        complaint_topics[user_id][topic] = 0
        if topic == "work":
            msg = "I notice you've been frustrated about work repeatedly. Instead of complaining, let's brainstorm solutions. What's one small change you could try? Or would you like to learn a new skill to change your career path?"
        elif topic == "relationship":
            msg = "You've mentioned relationship struggles many times. Let's shift from complaining to healing. What's something you can do today to improve your own well‑being, regardless of the other person?"
        elif topic == "money":
            msg = "Money worries are tough. Instead of focusing on the problem, let's look for one actionable step – like budgeting or learning a side skill. Would you like that?"
        else:
            msg = "You've shared similar frustrations several times. How about we try to turn that energy into a solution? What's one small thing you can do differently?"
        return True, msg
    return False, ""