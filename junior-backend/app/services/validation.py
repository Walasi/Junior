def needs_validation(message: str) -> bool:
    """Detect if user is fishing for validation or avoiding self-validation."""
    lower = message.lower()
    validation_seeking = ["am i good", "did i do right", "is that ok", "tell me i'm", "do you think i'm"]
    self_doubt = ["i'm not sure", "i doubt", "maybe i'm wrong"]
    compliment_seeking = ["i'm the best", "i'm great at", "look what i did"]
    return any(p in lower for p in validation_seeking) or any(d in lower for d in self_doubt)

def should_encourage_self_validation(message: str) -> bool:
    """Return True if user seeks validation but we should turn it inward."""
    lower = message.lower()
    return "tell me" in lower or "what do you think" in lower