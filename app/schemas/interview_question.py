from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId


class PyObjectId(str):
    # Custom type for handling MongoDB ObjectId in Pydantic models
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class QuestionBase(BaseModel):
    # Base schema for an interview question
    category: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Category of the question"
    )
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Interview question"
    )
    tips: Optional[str] = Field(
        None, description="Tips for answering the question"
    )
    example_answer: Optional[str] = Field(
        None, description="Example answer for reference"
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
        orm_mode = True  # Enables ORM compatibility
        json_encoders = {ObjectId: str}  # Convert MongoDB ObjectId to string
        # Allows using "_id" as "id" in responses
        allow_population_by_field_name = True


class QuestionUpdate(BaseModel):
    # Schema for updating an existing question (partial updates)
    category: Optional[str] = Field(
        None, min_length=2, max_length=50, description="Updated category"
    )
    question: Optional[str] = Field(
        None,
        min_length=5,
        max_length=500,
        description="Updated interview question"
    )
    tips: Optional[str] = Field(None, description="Updated tips for answering")
    example_answer: Optional[str] = Field(
        None, description="Updated example answer"
    )
