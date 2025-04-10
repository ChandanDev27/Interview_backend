from pydantic import BaseModel, Field, field_validator, FieldValidationInfo
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


# Schema for AI-generated feedback entries
class AIFeedbackEntry(BaseModel):
    feedback: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Schema for API response
class InterviewResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    questions: List[str]
    responses: List[Optional[str]] = Field(default_factory=list)
    status: InterviewStatus = InterviewStatus.PENDING
    status_history: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ai_feedback: List[AIFeedbackEntry] = Field(default_factory=list)

    @field_validator("responses", mode="before")
    @classmethod
    def match_response_list(cls, v, info: FieldValidationInfo):
        if not v and "questions" in info.data:
            return [None] * len(info.data["questions"])
        return v

    class Config:
        populate_by_name = True
        from_attributes = True


# Schema for submitting interview responses
class ResponseSubmission(BaseModel):
    responses: List[str]


# Schema for AI analysis feedback
class AIAnalysis(BaseModel):
    feedback: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
