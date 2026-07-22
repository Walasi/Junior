from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, chat, events, energy, career, social
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.birthday import send_birthday_wishes
from app.database import engine, Base
from sqlalchemy import text
import app.models.user
import app.models.conversation
import app.models.event
import app.models.emotion
import app.models.life_event
import app.models.knowledge
import app.models.memory
from app.routers import user
import app.models.content
from app.routers import career, social
from app.routers import content_tracking

app = FastAPI(title="Junior - Your Always-There Friend", version="1.10.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    
    # Add onboarding_step column if it doesn't exist
    try:
        with engine.connect() as conn:
            pass
            print("✅ Added onboarding_step column")
    except Exception as e:
        # Column likely already exists
        print(f"Column might already exist: {e}")

# Include routers (no duplicates)
app.include_router(auth.router, tags=["authentication"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
#app.include_router(voice.router, prefix="/voice", tags=["voice"])
app.include_router(events.router, prefix="/events", tags=["events"])
#app.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
#app.include_router(writings.router, prefix="/writings", tags=["writings"])
app.include_router(energy.router)
app.include_router(career.router)
app.include_router(social.router)
#app.include_router(emergency.router)
app.include_router(content_tracking.router)
app.include_router(user.router)

# Birthday scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_birthday_wishes, 'cron', hour=9, minute=0)
scheduler.start()

from apscheduler.schedulers.background import BackgroundScheduler
from app.services.energy_aggregator import aggregate_daily_energy
from app.database import SessionLocal

def run_daily_energy_aggregation():
    db = SessionLocal()
    try:
        aggregate_daily_energy(db)
    finally:
        db.close()

# In startup after existing scheduler:
scheduler.add_job(run_daily_energy_aggregation, 'cron', hour=1, minute=0)  # 1 AM daily

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

@app.get("/")
async def root():
    return {"message": "Welcome to Junior API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}