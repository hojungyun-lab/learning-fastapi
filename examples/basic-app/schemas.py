# schemas.py — Pydantic 요청/응답 스키마
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """아이템 생성 요청"""
    name: str = Field(..., min_length=1, max_length=100, examples=["노트북"])
    price: float = Field(..., gt=0, examples=[1200000])
    description: str | None = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list, examples=[["전자", "컴퓨터"]])


class ItemUpdate(BaseModel):
    """아이템 부분 수정 요청 — 모든 필드 선택적"""
    name: str | None = Field(None, min_length=1, max_length=100)
    price: float | None = Field(None, gt=0)
    description: str | None = None
    tags: list[str] | None = None


class ItemResponse(BaseModel):
    """아이템 응답"""
    id: int
    name: str
    price: float
    description: str | None = None
    tags: list[str] = []
