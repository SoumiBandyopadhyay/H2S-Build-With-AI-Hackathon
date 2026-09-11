from sqlalchemy import Column, Integer, String, Float, DateTime, Text # pyright: ignore[reportMissingImports]
from datetime import datetime
from database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    language = Column(String, default="en")
    state = Column(String, index=True)
    district = Column(String, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    category = Column(String, index=True)
    urgency = Column(Integer, default=3)
    sentiment = Column(String, default="neutral")
    summary = Column(Text)
    priority_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)