from pydantic import BaseModel, Field, EmailStr, HttpUrl, SecretStr
from typing import Optional


class User(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=50, description="User's full name"
    )
    email: EmailStr = Field(
        ..., description="User's email address"
        )
    imageUrl: HttpUrl = Field(
        ..., description="URL of the user's profile image"
        )


class UserCreate(BaseModel):
    client_id: str = Field(
        ..., min_length=5, description="Unique client identifier"
        )
    client_secret: SecretStr = Field(
        ..., min_length=8, description="Client secret (hashed)"
        )
    role: Optional[str] = Field(
        default="candidate", description="User role (default: candidate)"
        )


class UserResponse(BaseModel):
    client_id: str
    roll: str

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    id: str
    username: str

    class Config:
        populate_by_name = True
