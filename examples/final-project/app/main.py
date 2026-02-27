# app/main.py — 앱 진입점
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.exceptions import AppException, app_exception_handler
from app.routers import auth, todos

logging.basicConfig(level=logging.INFO if settings.debug else logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 테이블 생성, 종료 시 정리"""
    Base.metadata.create_all(bind=engine)
    logger.info("데이터베이스 테이블 초기화 완료")
    yield
    logger.info("앱 종료")


app = FastAPI(
    title=settings.app_name,
    description="FastAPI 실전 학습 프로젝트 — Todo API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── 예외 핸들러 ──
app.add_exception_handler(AppException, app_exception_handler)

# ── 미들웨어 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response


# ── 라우터 등록 ──
app.include_router(auth.router)
app.include_router(todos.router)


# ── 헬스체크 ──
@app.get("/health")
def health_check():
    return {"status": "healthy"}
