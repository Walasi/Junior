from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)   # for SMS
    email = Column(String, nullable=True)   # for email
    relationship = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)