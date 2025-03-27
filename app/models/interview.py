from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class Interview(BaseModel):
    id: Optional[str] = None  # ✅ Changed to None, MongoDB will generate `_id`
    user_id: str
    questions: List[str]
    responses: List[Optional[str]] = Field(default_factory=list)
    feedback: Optional[str] = None
    ai_feedback: List[dict] = Field(default_factory=list)
    status: Literal["pending", "completed"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status_history: List[str] = Field(default_factory=list)

    @field_validator("responses", mode="before")
    @classmethod
    def set_default_responses(cls, v, values):
        if not v and "questions" in values:
            return [None] * len(values["questions"])
        return v

    @field_validator("status", mode="before")
    @classmethod
    def track_status_change(cls, v, values):
        if "status_history" in values and isinstance(values["status_history"], list):
            values["status_history"].append(v)
        return v

    class Config:
        populate_by_name = True
        from_attributes = True
