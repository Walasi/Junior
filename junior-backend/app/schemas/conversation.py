from pydantic import BaseModel
from datetime import datetime

class ConversationBase(BaseModel):
    message: str

class ConversationCreate(ConversationBase):
    pass

class ConversationOut(ConversationBase):
    id: int
    user_id: int
    response: str
    timestamp: datetime

    class Config:
        from_attributes = True