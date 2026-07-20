import json
import openai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "qwen/qwen3-vl-235b-a22b-thinking"

client = openai.OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

def extract_skills_from_message(message: str) -> list:
    """
    Use OpenRouter to extract skills from user message.
    Returns a list of skill strings.
    """
    if not OPENROUTER_API_KEY:
        return []
    try:
        prompt = f"""Extract professional, technical, or soft skills mentioned in this message.
Return only a JSON list of strings, nothing else. If no skills, return empty list.

Message: {message}
Skills:"""
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150,
        )
        content = completion.choices[0].message.content.strip()
        # Try to parse JSON
        if content.startswith("["):
            skills = json.loads(content)
        else:
            # Fallback: split by commas
            skills = [s.strip() for s in content.split(",") if s.strip()]
        return skills[:5]   # limit
    except Exception as e:
        logger.error(f"Skill extraction failed: {e}")
        return []