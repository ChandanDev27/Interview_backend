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
