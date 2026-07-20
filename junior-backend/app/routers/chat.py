from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.deps import get_current_user
from app.database import get_db
from app.core.config import settings
from app.core.danger import DANGER_KEYWORDS
from textblob import TextBlob
import openai
import logging
from typing import Optional, List, Dict, Tuple
from app.models.conversation_thread import ConversationThread

router = APIRouter()

# --- Define logger FIRST ---
logger = logging.getLogger(__name__)

# ---------- LLM CONFIG ----------
# Prefer Fireworks (Gemma 4) if API key is set, otherwise use OpenRouter
FIREWORKS_MODEL = "accounts/waldisone-89uxvz2x04/deployments/vvwu3t2j"

def call_llm(messages, temperature=0.7, max_tokens=500):
    """Use deployed Gemma 4, fallback to OpenRouter if needed."""
    try:
        if settings.fireworks_api_key:
            client = openai.OpenAI(
                base_url=settings.fireworks_base_url,
                api_key=settings.fireworks_api_key
            )
            completion = client.chat.completions.create(
                model=FIREWORKS_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            logger.info("Used deployed Gemma 4 (Fireworks)")
            return completion.choices[0].message.content
    except Exception as e:
        logger.warning(f"Deployed model failed: {e}. Falling back to OpenRouter.")

    # Fallback to OpenRouter
    if settings.openrouter_api_key:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key
        )
        completion = client.chat.completions.create(
            model="qwen/qwen3-vl-235b-a22b-thinking",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info("Used OpenRouter (fallback)")
        return completion.choices[0].message.content

    return "I'm here for you. Tell me more."


# ---------- Sentiment ----------
def analyze_sentiment(conversation_id: int, text: str):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        db_conversation = db.query(models.conversation.Conversation).filter(
            models.conversation.Conversation.id == conversation_id
        ).first()
        if db_conversation:
            db_conversation.sentiment_score = sentiment
            db.commit()
    except Exception as e:
        logger.error(f"Sentiment failed: {e}")
    finally:
        db.close()

def contains_danger(text: str) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in DANGER_KEYWORDS)

# ---------- Prompt building ----------
def build_system_prompt(triad_mode: bool = False, age_group: str = "adult") -> str:
    base_prompt = """You are Junior, a supportive, empathetic friend. Your role is to help users process their thoughts and feelings.

**Fear Reframing Guidelines:**
- When you detect fear, anxiety, or self-doubt (e.g., "I can't", "I'm afraid", "What if I fail"), do NOT dismiss it.
- Acknowledge the fear with warmth: "It sounds like you're worried about... That's completely understandable."
- Gently reframe with curiosity: "What would you do if you weren't afraid?" or "What's one tiny, safe step you could take?"
- Avoid toxic positivity. Validate the emotion first.

**Triad Thinking Guidelines (Thoughts → Emotions → Behaviors):**
- After understanding the user's situation, help them see the connection:
  1. What thought triggered this feeling?
  2. How did that emotion lead to a certain action (or inaction)?
  3. Suggest one small shift in thought that could change the outcome.
- Use the triad only when relevant – don't force it.

Keep responses warm, concise (2-4 sentences), and practical. Ask clarifying questions if the context is unclear."""

    if triad_mode:
        base_prompt += "\n\n**Currently in TRIAD MODE:** Always apply the Thoughts-Emotions-Behaviors framework in your response."

    age_prompts = {
        "child": "\n\nThe user is a child. Keep responses very simple, playful, and creative. Use short sentences. Encourage imagination and games.",
        "teenager": "\n\nThe user is a teenager. Be respectful, cool, and non-judgmental. Validate their emotions but gently challenge harmful ideas. Use relatable examples.",
        "adult": "\n\nThe user is an adult. Be practical, empathetic, and solution-oriented. Offer career and life advice when appropriate.",
        "aged": "\n\nThe user is elderly. Be gentle, patient, and wise. Focus on healing and meaningful memories. Offer companionship."
    }
    base_prompt += age_prompts.get(age_group, age_prompts["adult"])
    return base_prompt

# ---------- Clarifying questions ----------
def needs_clarification(user_message: str, recent_history: List[str]) -> Tuple[bool, Optional[str]]:
    words = user_message.split()
    if len(words) < 5:
        return True, "Could you tell me a bit more about what's on your mind?"
    vague_patterns = ["bad", "good", "okay", "fine", "not good", "not great"]
    if any(phrase in user_message.lower() for phrase in vague_patterns) and len(recent_history) == 0:
        return True, "I want to understand you better. What's been happening lately?"
    return False, None

def query_llm_with_clarification(messages: List[Dict], user_message: str, history: List[str], ask_clarifying: bool = True) -> str:
    if ask_clarifying:
        needs_q, question = needs_clarification(user_message, history)
        if needs_q:
            return question
    return call_llm(messages)

# ---------- New service imports ----------
from app.services.age_group import get_age_group
from app.services.complaint_tracker import track_complaint
from app.services.web_search import search_web
from app.services.why_game import continue_why_game
from app.services.validation import needs_validation, should_encourage_self_validation
from app.services.humor import is_naive_funny
from app.services.memory_moments import capture_important_moment

# ---------- Thread endpoints ----------
@router.get("/threads")
def get_threads(db: Session = Depends(get_db), current_user: models.user.User = Depends(get_current_user)):
    threads = db.query(ConversationThread).filter(ConversationThread.user_id == current_user.id).order_by(ConversationThread.created_at.desc()).all()
    return threads

@router.post("/threads")
def create_thread(db: Session = Depends(get_db), current_user: models.user.User = Depends(get_current_user)):
    thread = ConversationThread(user_id=current_user.id, title="New Chat")
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread

@router.get("/threads/{thread_id}/messages")
def get_thread_messages(thread_id: int, db: Session = Depends(get_db), current_user: models.user.User = Depends(get_current_user)):
    messages = db.query(models.conversation.Conversation).filter(
        models.conversation.Conversation.thread_id == thread_id,
        models.conversation.Conversation.user_id == current_user.id
    ).order_by(models.conversation.Conversation.timestamp.asc()).all()
    return messages

# ---------- Main chat endpoint ----------
@router.post("", response_model=schemas.conversation.ConversationOut)
async def chat(
    conversation: schemas.conversation.ConversationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user),
    triad_mode: bool = False,
    ask_clarifying: bool = True,
    thread_id: Optional[int] = None
):
    # 1. Get or create thread
    if thread_id is None:
        thread = ConversationThread(user_id=current_user.id, title="New Chat")
        db.add(thread)
        db.commit()
        db.refresh(thread)
        thread_id = thread.id
    else:
        thread = db.query(ConversationThread).filter(
            ConversationThread.id == thread_id,
            ConversationThread.user_id == current_user.id
        ).first()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

    # 2. Store user message
    db_conversation = models.conversation.Conversation(
        user_id=current_user.id,
        message=conversation.message,
        response="",
        thread_id=thread_id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)

    # 3. Update thread title if still "New Chat"
    if thread.title == "New Chat" and conversation.message:
        thread.title = conversation.message[:50] + ("..." if len(conversation.message) > 50 else "")
        db.commit()

    # 4. Sentiment background task
    background_tasks.add_task(analyze_sentiment, db_conversation.id, conversation.message)

    # ========== ONBOARDING LOGIC ==========
    from app.services.onboarding import should_advance_step, get_onboarding_question
    user_step = current_user.onboarding_step if current_user.onboarding_step is not None else 0

    if user_step == 0:
        current_user.onboarding_step = 1
        db.commit()
        first_question = get_onboarding_question(1)
        db_conversation.response = first_question
        db.commit()
        return db_conversation

    if 1 <= user_step <= 5:
        if should_advance_step(conversation.message, user_step):
            new_step = user_step + 1
            if new_step > 5:
                current_user.onboarding_step = -1
                db.commit()
            else:
                current_user.onboarding_step = new_step
                db.commit()
                context = {}
                if user_step == 1:
                    context["name"] = conversation.message.strip()
                next_question = get_onboarding_question(new_step, context)
                db_conversation.response = next_question
                db.commit()
                return db_conversation
        else:
            repeat_question = get_onboarding_question(user_step)
            db_conversation.response = repeat_question
            db.commit()
            return db_conversation

    # ========== NEW FEATURE CHECKS ==========

    # 1. Web search (async, but we'll call it using await for simplicity)
    if "search" in conversation.message.lower() or "look up" in conversation.message.lower():
        try:
            web_answer = await search_web(conversation.message)
        except Exception as e:
            logger.error(f"Web search error: {e}")
            web_answer = "⚠️ Web search failed. Please try again later."
        reply = f"🔍 {web_answer}"
        db_conversation.response = reply
        db.commit()
        return db_conversation

    # 2. Why game active
    if current_user.why_game_state and current_user.why_game_state.get("active"):
        next_q, still_active = continue_why_game(db, current_user, conversation.message)
        if still_active:
            db_conversation.response = next_q
            db.commit()
            return db_conversation

    # 3. Complaint tracking
    should_redirect, redirect_msg = track_complaint(current_user.id, conversation.message)
    if should_redirect:
        db_conversation.response = redirect_msg
        db.commit()
        return db_conversation

    # 4. Humor detection
    is_funny, funny_msg = is_naive_funny(conversation.message)
    if is_funny:
        reply = funny_msg + " But hey, I like your imagination! Let's talk more."
        db_conversation.response = reply
        db.commit()
        return db_conversation

    # 5. Validation detection
    if needs_validation(conversation.message):
        if should_encourage_self_validation(conversation.message):
            reply = "That's a good question. What do YOU think about it? Your own opinion matters most."
        else:
            reply = "I see you're looking for reassurance. You're doing great. Let's focus on what you can do next."
        db_conversation.response = reply
        db.commit()
        return db_conversation

    # 6. Capture important moments (sync sentiment)
    blob = TextBlob(conversation.message)
    sentiment = blob.sentiment.polarity
    capture_important_moment(db, current_user.id, conversation.message, sentiment)

    # ========== DANGER CHECK ==========
    if contains_danger(conversation.message):
        from app.services.alerts import alert_emergency_contacts
        contacts = db.query(models.emergency_contact.EmergencyContact).filter(
            models.emergency_contact.EmergencyContact.user_id == current_user.id
        ).all()
        if contacts:
            alert_emergency_contacts(contacts, "crisis message", current_user.username, "")
        reply = "I'm really concerned. Please reach out to a helpline immediately."
        db_conversation.response = reply
        db.commit()
        return db_conversation

    # ========== NORMAL LLM RESPONSE ==========
    age_grp = get_age_group(current_user.date_of_birth)
    system_prompt = build_system_prompt(triad_mode=triad_mode, age_group=age_grp)

    past = db.query(models.conversation.Conversation).filter(
        models.conversation.Conversation.user_id == current_user.id,
        models.conversation.Conversation.thread_id == thread_id
    ).order_by(models.conversation.Conversation.timestamp.desc()).limit(10).all()
    past.reverse()

    messages = [{"role": "system", "content": system_prompt}]
    for conv in past:
        messages.append({"role": "user", "content": conv.message})
        if conv.response:
            messages.append({"role": "assistant", "content": conv.response})
    messages.append({"role": "user", "content": conversation.message})

    history_texts = [conv.message for conv in past]
    reply = query_llm_with_clarification(messages, conversation.message, history_texts, ask_clarifying)

    db_conversation.response = reply
    db.commit()
    db.refresh(db_conversation)
    return db_conversation