from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CandidateAnswer(BaseModel):
    candidate_id: str
    question_id: str
    answer_text: Optional[str] = None
    answer_audio: Optional[str] = None
    answer_video: Optional[str] = None
    ai_feedback: Optional[str] = None


class CandidateAnswerDB(CandidateAnswer):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
