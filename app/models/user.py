from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    ADMIN = "admin"


class User(BaseModel):
    id: Optional[str]
    client_id: str
    Name: str
    email: EmailStr
    role: UserRole = UserRole.CANDIDATE
    hashed_password: str
    avatar_url: Optional[str] = Field(
        default=None,
        example="https://example.com/avatars/user123.png"
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    client_id: str
    client_secret: Optional[str] = None
    role: UserRole = UserRole.CANDIDATE


class UserResponse(BaseModel):
    client_id: str
    role: UserRole


class UserSchema(BaseModel):
    id: str
    username: str

    class Config:
        populate_by_name = True
        from_attributes = True
