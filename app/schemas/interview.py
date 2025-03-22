from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum


# Enum for interview status
class InterviewStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


# Schema for creating an interview
class InterviewCreate(BaseModel):
    user_id: str  # Use string type for user_id instead of PyObjectId
    questions: List[str]

    class Config:
        arbitrary_types_allowed = True


# Schema for API response
class InterviewResponse(BaseModel):
    id: str = Field(..., alias="_id")  # Use string type for id instead of PyObjectId
    user_id: str
    questions: List[str]
    responses: List[str] = Field(default_factory=list)
    feedback: Optional[str] = None
    status: InterviewStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


# Schema for submitting interview responses
class ResponseSubmission(BaseModel):
    responses: List[str]


# Schema for AI analysis feedback
class AIAnalysis(BaseModel):
    feedback: str
