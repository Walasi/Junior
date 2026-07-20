from typing import Dict, Optional

ONBOARDING_QUESTIONS = {
    1: "Hey there! I'm Junior. What's your name? (Or what should I call you?)",
    2: "Nice to meet you, {name}! How are you feeling today? 😊",
    3: "What brings you here? Is there something specific you'd like to talk about or work on?",
    4: "That's really helpful to know. Just so I understand you better – what's something you enjoy doing in your free time?",
    5: "Thanks for sharing! One last thing – do you have any worries or hopes for our conversations?",
}

def get_onboarding_question(step: int, context: Optional[Dict] = None) -> str:
    """Return the onboarding question for the given step, with optional variable substitution."""
    question = ONBOARDING_QUESTIONS.get(step, "Let's start our conversation. How can I support you today?")
    if context and step == 2 and "name" in context:
        question = question.format(name=context["name"])
    return question

def is_onboarding_complete(step: int) -> bool:
    return step == -1

def should_advance_step(user_message: str, current_step: int) -> bool:
    """
    Decide whether to move to the next onboarding step.
    Returns True if the user provided a meaningful answer.
    """
    msg = user_message.strip()
    if not msg:
        return False

    # Minimum length: at least 2 characters
    if len(msg) < 2:
        return False

    # For step 1 (name), also check that name is not too short or just numbers
    if current_step == 1:
        # Name should be alphabetic or alphanumeric, at least 2 chars, not just digits
        if msg.isdigit() or len(msg) < 2:
            return False
        # Optionally prevent obvious placeholders like "test", "user", etc.
        common_placeholders = ["test", "user", "name", "unknown", "none", "n/a"]
        if msg.lower() in common_placeholders:
            return False
        return True

    # For other steps, require at least 3 words OR more than 8 characters
    words = msg.split()
    if len(words) >= 3 or len(msg) > 8:
        return True

    # If the message is too generic (like "ok", "fine", "good") we might still accept,
    # but we can be a bit more lenient. Let's accept if it's not just a single common word.
    short_common = {"ok", "okay", "good", "bad", "fine", "sure", "yes", "no", "maybe"}
    if msg.lower() in short_common and len(words) == 1:
        return False

    return True