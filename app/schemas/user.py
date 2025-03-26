from pydantic import BaseModel, Field, EmailStr, HttpUrl


class User(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=50, description="User's full name"
    )
    email: EmailStr = Field(
        ..., description="User's email address"
        )
    imageUrl: HttpUrl = Field(
        ..., description="URL of the user's profile image"
        )


class UserCreate(BaseModel):
    client_id: str
    client_secret: str
    role: str


class UserResponse(BaseModel):
    client_id: str
    role: str

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    id: str
    username: str

    class Config:
        populate_by_name = True
