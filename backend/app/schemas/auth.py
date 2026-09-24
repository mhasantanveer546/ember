"""
Ember Backend — Auth Schemas

Pydantic models defining the exact shape of auth-related requests and
responses. FastAPI uses these to validate incoming JSON automatically
(a request missing `password`, or with a non-email `email`, is rejected
with a 422 before the route function even runs) and to generate the
/docs schema.
"""

import uuid

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    """What we return about a user — never includes hashed_password."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: EmailStr