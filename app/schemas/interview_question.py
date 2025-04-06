from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId as BsonObjectId
from datetime import datetime


class PyObjectId(str):
    """
    Custom type for MongoDB ObjectId.
    Ensures Pydantic models work smoothly with BSON ObjectId in MongoDB documents.
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not BsonObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class QuestionBase(BaseModel):
    # Base schema for an interview question
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


class QuestionCreate(QuestionBase):
    # Schema for creating a new question
    pass


class QuestionResponse(QuestionBase):
    # Schema for returning a question response from the API
    id: PyObjectId = Field(
        ...,
        alias="_id",
        title="ID",
        description="Unique identifier of the question"
    )

    class Config:
        orm_mode = True
        json_encoders = {BsonObjectId: str}
        allow_population_by_field_name = True


class QuestionUpdate(BaseModel):
    # Schema for updating an existing question (partial updates)
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


class QuestionModel(QuestionResponse):
    # Final DB model used in MongoDB collections
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the question was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the question was last updated"
    )
