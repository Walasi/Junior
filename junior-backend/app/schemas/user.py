from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    date_of_birth: Optional[datetime] = None

class UserCreate(UserBase):
    password: str
    
    @validator('email', pre=True)
    def empty_email_to_none(cls, v):
        if v == "":
            return None
        return v

    @validator('password')
    def password_not_too_long(cls, v):
        # bcrypt maximum is 72 bytes
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be at most 72 bytes (roughly 72 characters)')
        return v
    
class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None