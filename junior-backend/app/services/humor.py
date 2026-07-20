import re

FUNNY_NAIVE_PATTERNS = [
    r"i think the earth is flat",
    r"i can fly if i try",
    r"money grows on trees",
    r"i'll become millionaire tomorrow",
    r"i don't need to sleep"
]

def is_naive_funny(message: str) -> tuple[bool, str]:
    """Return (is_funny, explanation)."""
    lower = message.lower()
    for pattern in FUNNY_NAIVE_PATTERNS:
        if re.search(pattern, lower):
            return True, f"That's a funny/naive thought! 😄 {pattern} is not quite true – let me explain..."
    return False, ""