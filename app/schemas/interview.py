from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# Enum for interview status
class InterviewStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


# Schema for creating an interview
class InterviewCreate(BaseModel):
    questions: List[str]

    class Config:
        from_attributes = True


class AIFeedbackEntry(BaseModel):
    feedback: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Schema for API response
class InterviewResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    questions: List[str]
    responses: List[str] = Field(default_factory=list)
    status: InterviewStatus
    status_history: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    ai_feedback: Optional[List[AIFeedbackEntry]] = Field(default_factory=list)


    class Config:
        populate_by_name = True
        from_attributes = True


# Schema for submitting interview responses
class ResponseSubmission(BaseModel):
    responses: List[str]


# Schema for AI analysis feedback
class AIAnalysis(BaseModel):
    feedback: str
