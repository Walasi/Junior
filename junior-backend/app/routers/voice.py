from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.deps import get_db
from app.models.user import User
from app.services.voice import VoiceService
import logging

router = APIRouter(prefix="/voice", tags=["Voice"])

logger = logging.getLogger(__name__)

@router.post("/enroll")
async def enroll_voice(
    user_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Enroll a voice print for the given user.
    Accepts an audio file (WAV, 16kHz mono recommended).
    """
    # Check user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Read audio file
    try:
        audio_bytes = await audio.read()
        # Optionally validate audio format/length here
        embedding = VoiceService.extract_embedding(audio_bytes)
    except Exception as e:
        logger.error(f"Voice enrollment failed: {e}")
        raise HTTPException(status_code=400, detail="Could not process audio")

    # Store embedding in user record
    user.voice_print = embedding  # if Vector column, it accepts list
    db.commit()

    return {"message": "Voice enrolled successfully", "embedding_length": len(embedding)}

@router.post("/identify")
async def identify_voice(
    user_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Test endpoint: compare uploaded audio with enrolled voice print.
    Returns similarity score and whether it's considered the primary user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.voice_print:
        raise HTTPException(status_code=400, detail="No voice enrolled for this user")

    try:
        audio_bytes = await audio.read()
        embedding = VoiceService.extract_embedding(audio_bytes)
    except Exception as e:
        logger.error(f"Voice identification failed: {e}")
        raise HTTPException(status_code=400, detail="Could not process audio")

    similarity = VoiceService.compare_embeddings(user.voice_print, embedding)
    # Threshold can be tuned (e.g., 0.7)
    is_primary = similarity >= 0.7

    return {
        "user_id": user_id,
        "similarity": similarity,
        "is_primary": is_primary,
        "threshold_used": 0.7
    }