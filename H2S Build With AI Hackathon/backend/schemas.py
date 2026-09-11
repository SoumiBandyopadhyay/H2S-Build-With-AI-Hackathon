from pydantic import BaseModel, ConfigDict # pyright: ignore[reportMissingImports]
from typing import Optional
from datetime import datetime


class ComplaintCreate(BaseModel):
    raw_text: str
    language: str = "en"
    state: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    raw_text: str
    language: str
    state: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: str
    urgency: int
    sentiment: str
    summary: str
    priority_score: float
    created_at: datetime