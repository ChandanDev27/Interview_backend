from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class User(BaseModel):
    client_id: str
    client_secret: str
    role: Literal["candidate", "admin"] = "candidate"
    is_admin: bool = False
    interviews: List[str] = Field(default_factory=list)


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
