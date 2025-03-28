from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class User(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    imageUrl: Optional[str] = Field(None, description="URL of the user's profile image")


class UserCreate(BaseModel):
    email: EmailStr
    role: str
    password: str


class UserResponse(BaseModel):
    id: Optional[str] = None
    client_id: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "605c72d9fc13ae7890000000",
                "client_id": "12345",
                "email": "user@example.com",
                "role": "candidate"
            }
        }


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword"
            }
        }


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
