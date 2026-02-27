# app/dependencies.py — 공통 의존성
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User

# 타입 별칭 — 전체 앱에서 재사용
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


class PaginationParams:
    """페이지네이션 파라미터"""
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
        limit: int = Query(20, ge=1, le=100, description="조회할 최대 항목 수"),
    ):
        self.skip = skip
        self.limit = limit


Pagination = Annotated[PaginationParams, Depends()]
