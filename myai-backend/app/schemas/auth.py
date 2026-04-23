from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    full_name: str | None = Field(default=None, max_length=120)


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class AuthRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_admin: bool


class AuthRegisterResponse(BaseModel):
    user: AuthUser


class AuthLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: AuthUser
