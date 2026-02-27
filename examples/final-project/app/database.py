# app/database.py — 데이터베이스 엔진 및 세션 설정
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False}  # SQLite 전용
    if "sqlite" in settings.database_url
    else {},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """요청마다 DB 세션을 생성하고 응답 후 닫습니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
