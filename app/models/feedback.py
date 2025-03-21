from pydantic import BaseModel, Field
from datetime import datetime


class Feedback(BaseModel):
    interview_id: str
    facial_score: float
    speech_score: float
    transcript: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
