from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Conversation Engine Schemas

class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    member_ids: list[int] = Field(min_length=1, max_length=49)


class ConversationResponse(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    member_ids: list[int]

    model_config = {"from_attributes": True}
