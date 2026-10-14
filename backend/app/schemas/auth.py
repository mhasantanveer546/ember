"""
Ember Backend — Auth Schemas

Pydantic models defining the exact shape of auth-related requests and
responses. FastAPI uses these to validate incoming JSON automatically
(a request missing `password`, or with a non-email `email`, is rejected
with a 422 before the route function even runs) and to generate the
/docs schema.
"""

import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


def _normalise_email(value: str) -> str:
    # "Alice@X.com" and "alice@x.com" are the same mailbox for practical
    # purposes; without this they could register twice or fail to log in.
    return value.strip().lower()


class UserRegister(BaseModel):
    email: EmailStr
    # bcrypt only uses the first 72 BYTES, so cap there (multi-byte characters count more).
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, v: str) -> str:
        return _normalise_email(v)

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes).")
        if v.strip() == "":
            raise ValueError("Password cannot be blank.")
        if len(set(v)) < 4:
            raise ValueError("Password is too repetitive.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, v: str) -> str:
        return _normalise_email(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(max_length=4096)


class LogoutRequest(BaseModel):
    """Optional body: also revoke the refresh token so a stolen one dies at logout."""

    refresh_token: str | None = Field(default=None, max_length=4096)


class UserPublic(BaseModel):
    """What we return about a user — never includes hashed_password."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: EmailStr