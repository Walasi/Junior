from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from app.database import Base

class DailyEnergy(Base):
    __tablename__ = "daily_energy"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    avg_sentiment = Column(Float, nullable=True)
    message_count = Column(Integer, default=0)
    energy_level = Column(String, nullable=True)  # Very Low, Low, Moderate, Good, High