from pydantic import BaseModel, Field
from typing import Optional, Literal


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: Literal["bearer"] = "bearer"

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenData(BaseModel):
    client_id: Optional[str] = Field(default=None, description="Client ID associated with the token")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "client_id": "12345"
            }
        }


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
