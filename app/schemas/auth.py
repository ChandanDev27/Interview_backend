from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class OTPRequest(BaseModel):
    email: EmailStr
    otp: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
