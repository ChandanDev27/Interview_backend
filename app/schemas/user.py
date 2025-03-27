from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class User(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    imageUrl: Optional[str] = Field(None, description="URL of the user's profile image")  # ✅ Changed HttpUrl to str


class UserCreate(BaseModel):
    client_id: str
    client_secret: str
    role: str


class UserResponse(BaseModel):
    client_id: str
    role: str

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    id: Optional[str] = None
    username: str

    class Config:
        populate_by_name = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str
