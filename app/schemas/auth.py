from pydantic import BaseModel, EmailStr


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
