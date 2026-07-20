from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    reminder_time: datetime

class EventCreate(EventBase):
    pass

class EventOut(EventBase):
    id: int
    user_id: int
    is_completed: bool

    class Config:
        from_attributes = True