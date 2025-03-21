from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum


# MongoDB ObjectId handling
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


# Enum for interview status
class InterviewStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


# Schema for creating an interview
class InterviewCreate(BaseModel):
    user_id: PyObjectId
    questions: List[str]


# Schema for API response
class InterviewResponse(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    questions: List[str]
    responses: List[str] = Field(default_factory=list)
    feedback: Optional[str] = None
    status: InterviewStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True


# Schema for submitting interview responses
class ResponseSubmission(BaseModel):
    responses: List[str]


# Schema for AI analysis feedback
class AIAnalysis(BaseModel):
    feedback: str
