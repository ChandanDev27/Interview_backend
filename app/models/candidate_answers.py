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

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "12345",
                "question_id": "abcde",
                "answer_text": "I am passionate about problem-solving.",
                "answer_audio": "/media/audio/answer1.mp3",
                "answer_video": "/media/video/answer1.mp4",
                "ai_feedback": "Good posture and clear speech."
            }
        }


class CandidateAnswerDB(CandidateAnswer):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None  # Optional: update when edits occur
