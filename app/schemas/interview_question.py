from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from bson import ObjectId as BsonObjectId
from datetime import datetime


# Helper for converting and validating ObjectId (optional use)
def validate_object_id(v: str) -> str:
    if not BsonObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId")
    return str(v)


class QuestionBase(BaseModel):
    category: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Category of the question",
        example="Technical"
    )
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Interview question",
        example="What is polymorphism in Object-Oriented Programming?"
    )
    tips: Optional[str] = Field(
        None,
        description="Tips for answering the question",
        example="Break down the concept and give real-world analogies."
    )
    example_answer: Optional[str] = Field(
        None,
        description="Example answer for reference",
        example="Polymorphism allows methods to do different things based on the object it is acting upon..."
    )

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v):
        return v.strip().title()


    @field_validator("tips", mode="before")
    @classmethod
    def convert_tips_list_to_string(cls, v):
        if isinstance(v, list):
            return " ".join(v)
        return v


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: str = Field(
        ...,
        alias="_id",
        description="Unique identifier of the question",
        example="605c72ef8f1b2c06d890e5d3"
    )

    class Config:
        json_encoders = {BsonObjectId: str}
        populate_by_name = True
        allow_population_by_field_name = True


class QuestionUpdate(BaseModel):
    category: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Updated category",
        example="HR"
    )
    question: Optional[str] = Field(
        None,
        min_length=5,
        max_length=500,
        description="Updated interview question",
        example="How do you handle conflict in a team?"
    )
    tips: Optional[str] = Field(
        None,
        description="Updated tips for answering",
        example="Be honest and share a structured approach like 'listen, understand, resolve.'"
    )
    example_answer: Optional[str] = Field(
        None,
        description="Updated example answer",
        example="In a past project, I resolved a misunderstanding by arranging a 1-on-1 meeting..."
    )

    @field_validator("tips", mode="before")
    @classmethod
    def convert_tips_list_to_string(cls, v):
        if isinstance(v, list):
            return " ".join(v)
        return v


class QuestionModel(QuestionResponse):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the question was created"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the question was last updated"
    )
