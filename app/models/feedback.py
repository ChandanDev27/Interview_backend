from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Feedback(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    interview_id: str
    facial_score: float = Field(..., ge=0.0, le=1.0)
    speech_score: float = Field(..., ge=0.0, le=1.0)
    transcript: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
