from pydantic import BaseModel, Field
from typing import List, Optional


class InterviewQuestion(BaseModel):
    category: str
    experience_level: str
    question: str
    tips: Optional[List[str]] = Field(default_factory=list)
    example_answer: Optional[str] = None
