from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.enums import UserRole 


class LoginRequest(BaseModel):
    email: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "your_password123"
            }
        }


class OTPRequest(BaseModel):
    email: EmailStr
    otp: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456",
                "new_password": "new_secure_password123"
            }
        }

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole = UserRole.candidate
    invite_token: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securePassword123!",
                "name": "John Doe",
                "invite_token": "eyJhbGciOi..."
            }
        }
