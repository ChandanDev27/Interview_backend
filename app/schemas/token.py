from pydantic import BaseModel, Field
from typing import Optional


class Token(BaseModel):
    access_token: str = Field(
        ..., min_length=1, description="JWT access token"
    )
    token_type: str = Field(
        ..., min_length=1, description="Type of token (usually 'bearer')"
    )


class TokenData(BaseModel):
    client_id: Optional[str] = Field(
        default=None, description="Client ID associated with the token"
    )


class UserSchema(BaseModel):
    id: str
    username: str

    class Config:
        populate_by_name = True
