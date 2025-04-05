from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class InterviewStatus(str, Enum):
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

    @field_validator("responses", mode="before")
    @classmethod
    def set_default_responses(cls, v, values):
        if not v and "questions" in values:
            return [None] * len(values["questions"])
        return v

    class Config:
        populate_by_name = True
        from_attributes = True
