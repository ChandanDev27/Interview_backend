from pydantic import BaseModel
from typing import Optional, Literal


class User(BaseModel):
    id: str
    username: str
    email: str


class UserCreate(BaseModel):
    client_id: str
    client_secret: Optional[str] = None
    role: Literal["candidate", "admin"] = "candidate"


class UserResponse(BaseModel):
    client_id: str
    role: Literal["candidate", "admin"]


class UserSchema(BaseModel):
    id: str
    username: str

    class Config:
        populate_by_name = True
        from_attributes = True
