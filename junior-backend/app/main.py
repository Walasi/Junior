from fastapi import FastAPI
from app.routers import auth

app = FastAPI(title="Junior - Your Always-There Friend", version="1.0.0")

app.include_router(auth.router, tags=["authentication"])

@app.get("/")
async def root():
    return {"message": "Welcome to Junior API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

