from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class User(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    image_url: Optional[str] = Field(None, description="URL of the user's profile image")


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")
    role: str = Field(..., description="User role (e.g., 'candidate', 'admin')")


class UserResponse(BaseModel):
    id: Optional[str] = Field(None, description="User ID")
    client_id: str = Field(..., description="OAuth client ID")
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    role: str = Field(..., description="User's role (e.g., 'candidate', 'admin')")
    avatar_url: Optional[str] = Field(None, description="URL of the user's avatar image")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "605c72d9fc13ae7890000000",
                "client_id": "12345",
                "name": "John Doe",
                "email": "user@example.com",
                "role": "candidate",
                "avatar_url": "/media/avatars/605c72d9fc13ae7890000000_avatar.png"
            }
        }


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jane.doe@example.com"
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword"
            }
        }


class AdminUserUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated full name")
    email: Optional[EmailStr] = Field(None, description="Updated email address")
    role: Optional[str] = Field(None, description="Updated role ('admin' or 'candidate')")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")


class OTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send OTP")


class OTPResponse(BaseModel):
    message: str = Field(..., description="Status message indicating OTP was sent")
