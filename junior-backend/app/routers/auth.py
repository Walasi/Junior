from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import schemas, models
from app.core.auth import get_password_hash, verify_password, create_access_token
from app.api.deps import get_db

router = APIRouter()

@router.post("/signup", response_model=schemas.user.UserOut)
def signup(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    db_user = db.query(models.user.User).filter(
        (models.user.User.username == user.username) | (models.user.User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.user.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        date_of_birth=user.date_of_birth
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.user.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.user.User).filter(models.user.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}