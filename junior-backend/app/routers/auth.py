from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app import schemas, models
from app.core.auth import get_password_hash, verify_password, create_access_token
from app.deps import get_db

router = APIRouter()

@router.post("/login", response_model=schemas.user.Token)
async def login(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
    else:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing credentials")
    user = db.query(models.user.User).filter(models.user.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", response_model=schemas.user.UserOut)
def signup(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.user.User).filter(models.user.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username taken")
    if user.email:
        existing_email = db.query(models.user.User).filter(models.user.User.email == user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email taken")
    hashed = get_password_hash(user.password)
    db_user = models.user.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed,
        date_of_birth=user.date_of_birth,
        onboarding_step=0,
        profile_data={}  # initialize empty
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/register", response_model=schemas.user.UserOut)
def register(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    return signup(user, db)