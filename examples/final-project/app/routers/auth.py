# app/routers/auth.py — 인증 라우터
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import verify_password, get_password_hash, create_access_token
from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import DuplicateError
from app.models import User
from app.schemas import UserCreate, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    """회원가입"""
    # 중복 검사
    if db.query(User).filter(User.username == user.username).first():
        raise DuplicateError("사용자 이름", user.username)
    if db.query(User).filter(User.email == user.email).first():
        raise DuplicateError("이메일", user.email)

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/token", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """로그인 — JWT 토큰 발급"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 이름 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser):
    """현재 로그인한 사용자 정보"""
    return current_user
