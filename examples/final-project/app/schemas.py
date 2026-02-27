# app/schemas.py — Pydantic 요청/응답 스키마
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


# ──────────────────────────────────────────────
# Auth 스키마
# ──────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ──────────────────────────────────────────────
# Todo 스키마
# ──────────────────────────────────────────────
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    priority: int = Field(0, ge=0, le=2)  # 0: 보통, 1: 높음, 2: 긴급


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None
    priority: int | None = Field(None, ge=0, le=2)


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    completed: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    owner_id: int

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    total: int
    items: list[TodoResponse]
