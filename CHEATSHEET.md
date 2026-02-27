# 📋 FastAPI 치트시트 — 빠른 참조 카드

> FastAPI 핵심 패턴을 빠르게 참조할 수 있는 요약본입니다.
> 자세한 설명은 `docs/` 디렉터리의 학습 문서를 참고하세요.

---

## 1. 앱 생성과 실행

```python
from fastapi import FastAPI

# 앱 인스턴스 생성
app = FastAPI(
    title="My API",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI (기본값)
    redoc_url="/redoc",     # ReDoc (기본값)
)

# 서버 실행: poetry run uvicorn main:app --reload --port 8000
```

---

## 2. 라우팅 (Routing)

```python
# HTTP 메서드별 데코레이터
@app.get("/items")                    # 목록 조회
@app.get("/items/{item_id}")          # 단건 조회
@app.post("/items", status_code=201)  # 생성
@app.put("/items/{item_id}")          # 전체 수정
@app.patch("/items/{item_id}")        # 부분 수정
@app.delete("/items/{item_id}", status_code=204)  # 삭제

# APIRouter로 라우트 분리
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users():
    ...

# main.py에서 라우터 등록
app.include_router(router)
```

---

## 3. 경로 파라미터 (Path Parameters)

```python
from fastapi import Path

@app.get("/items/{item_id}")
def get_item(
    item_id: int = Path(..., ge=1, description="아이템 ID"),
    # ...  → 필수 파라미터
    # ge=1 → 1 이상만 허용
):
    return {"item_id": item_id}
```

---

## 4. 쿼리 파라미터 (Query Parameters)

```python
from fastapi import Query

@app.get("/items")
def list_items(
    skip: int = Query(0, ge=0),           # 기본값 0, 0 이상
    limit: int = Query(10, le=100),       # 기본값 10, 100 이하
    q: str | None = Query(None, min_length=1),  # 선택적 검색어
):
    return {"skip": skip, "limit": limit, "q": q}
```

---

## 5. Pydantic 모델 (요청/응답 스키마)

```python
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# 요청 스키마
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["노트북"])
    price: float = Field(..., gt=0, description="가격 (0 초과)")
    tags: list[str] = Field(default_factory=list)

# 응답 스키마
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    created_at: datetime

    model_config = {"from_attributes": True}  # ORM 객체 → Pydantic 변환 허용

# 부분 수정 스키마
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
```

---

## 6. 요청 본문 (Request Body)

```python
@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate):  # JSON body 자동 파싱
    return {"id": 1, **item.model_dump()}

# 여러 바디 파라미터
from fastapi import Body

@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    item: ItemCreate,
    note: str = Body(None, embed=True),  # 추가 필드
):
    ...
```

---

## 7. 응답 모델과 상태 코드

```python
from fastapi.responses import JSONResponse

# response_model로 응답 필터링
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    return db_item  # ORM 객체 → ItemResponse 필드만 직렬화

# 다중 응답 정의 (OpenAPI 문서용)
@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    responses={
        404: {"description": "아이템을 찾을 수 없음"},
    },
)
def get_item(item_id: int):
    ...
```

---

## 8. 의존성 주입 (Dependency Injection)

```python
from fastapi import Depends
from typing import Annotated

# 함수형 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db  # yield 이후는 응답 완료 후 실행 (정리 로직)
    finally:
        db.close()

DbSession = Annotated[Session, Depends(get_db)]

# 라우트에서 사용
@app.get("/items")
def list_items(db: DbSession):
    return db.query(Item).all()

# 의존성 체이닝
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    ...

CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/me")
def read_me(user: CurrentUser):
    return user
```

---

## 9. 인증 (Authentication)

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# JWT 토큰 생성
def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# JWT 토큰 검증
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

# 로그인 엔드포인트
@app.post("/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # 사용자 인증 후 토큰 발급
    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}
```

---

## 10. 에러 핸들링 (Error Handling)

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request

# 기본 HTTP 예외
raise HTTPException(status_code=404, detail="Item not found")
raise HTTPException(status_code=403, detail="Not authorized", headers={"X-Error": "forbidden"})

# 커스텀 예외 클래스 + 핸들러
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id

@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Item {exc.item_id} not found"},
    )

# Pydantic 검증 에러 커스터마이징
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
```

---

## 11. 미들웨어 (Middleware)

```python
from fastapi.middleware.cors import CORSMiddleware
import time

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 허용할 도메인
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 커스텀 미들웨어 (처리 시간 측정)
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Process-Time"] = str(duration)
    return response
```

---

## 12. 백그라운드 태스크 (Background Tasks)

```python
from fastapi import BackgroundTasks

def send_notification(email: str, message: str):
    # 이메일 발송 등 시간이 걸리는 작업
    ...

@app.post("/orders")
def create_order(order: OrderCreate, background_tasks: BackgroundTasks):
    # 주문 생성 로직
    new_order = save_order(order)
    # 응답 반환 후 백그라운드에서 실행
    background_tasks.add_task(send_notification, order.email, "주문 완료")
    return new_order
```

---

## 13. 파일 업로드

```python
from fastapi import File, UploadFile

# 단일 파일 업로드
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}

# 다중 파일 업로드
@app.post("/uploads")
async def upload_files(files: list[UploadFile] = File(...)):
    return [{"filename": f.filename} for f in files]
```

---

## 14. 데이터베이스 (SQLAlchemy 2.0)

```python
from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# 엔진 및 세션
engine = create_engine("sqlite:///./app.db", echo=True)
SessionLocal = sessionmaker(bind=engine)

# 모델 정의 (Mapped 스타일)
class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float]
    is_active: Mapped[bool] = mapped_column(default=True)

# 테이블 생성
Base.metadata.create_all(bind=engine)

# CRUD 함수
def get_items(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: ItemCreate):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

---

## 15. 테스팅

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_items():
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_item():
    response = client.post("/items", json={"name": "Test", "price": 100.0})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test"

# 의존성 오버라이드 (DB 격리 테스트)
from main import get_db

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

---

## 16. Lifespan (앱 시작/종료)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 실행
    print("Starting up...")
    yield
    # 앱 종료 시 실행
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
```

---

## 17. 배포 (Docker)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Poetry 설치 및 의존성 복사
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 빌드 및 실행
docker build -t my-fastapi-app .
docker run -p 8000:8000 my-fastapi-app
```
