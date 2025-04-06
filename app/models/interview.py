from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class InterviewQuestion(BaseModel):
    category: str
    experience_level: str
    question: str
    tips: Optional[List[str]] = Field(default_factory=list)
    example_answer: Optional[str] = None


class InterviewQuestionDB(InterviewQuestion):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class InterviewStatus(str):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


class AIFeedbackEntry(BaseModel):
    feedback: str
    timestamp: datetime


class Interview(BaseModel):
    id: Optional[str] = None
    user_id: str
    questions: List[str]
    responses: List[Optional[str]] = Field(default_factory=list)
    feedback: Optional[str] = None
    ai_feedback: List[AIFeedbackEntry] = Field(default_factory=list)
    status: InterviewStatus = InterviewStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status_history: List[str] = Field(default_factory=list)

    @classmethod
    def set_default_responses(cls, v, values):
        if not v and "questions" in values:
            return [None] * len(values["questions"])
        return v

    class Config:
        populate_by_name = True
        from_attributes = True


class InterviewDB(Interview):
    id: str = Field(..., alias="_id")


class InterviewUpdate(BaseModel):
    feedback: Optional[str]
    ai_feedback: Optional[List[AIFeedbackEntry]]
    status: Optional[InterviewStatus]
    updated_at: datetime = Field(default_factory=datetime.utcnow)
