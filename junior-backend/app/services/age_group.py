from datetime import date
from typing import Optional

def get_age_group(birth_date: Optional[date]) -> str:
    """Return age group based on birth date."""
    if not birth_date:
        return "adult"  # default
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if age < 13:
        return "child"
    elif age < 20:
        return "teenager"
    elif age < 65:
        return "adult"
    else:
        return "aged"

def get_system_prompt_extension(age_group: str) -> str:
    """Return additional system prompt based on age group."""
    prompts = {
        "child": (
            "The user is a child. Keep responses very simple, playful, and creative. "
            "Use short sentences. Encourage imagination and games. Avoid heavy topics."
        ),
        "teenager": (
            "The user is a teenager. They may feel misunderstood or overconfident. "
            "Be respectful, cool, and non-judgmental. Validate their emotions but gently challenge harmful ideas. "
            "Use relatable examples (school, friends, social media)."
        ),
        "adult": (
            "The user is an adult. They likely face work, relationship, or financial stress. "
            "Be practical, empathetic, and solution-oriented. Offer career and life advice when appropriate."
        ),
        "aged": (
            "The user is elderly. They may deal with health, loneliness, or reflection. "
            "Be gentle, patient, and wise. Focus on healing and meaningful memories. "
            "Offer companionship and respect for their life experience."
        )
    }
    return prompts.get(age_group, prompts["adult"])