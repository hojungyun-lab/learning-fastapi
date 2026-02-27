# 🗄️ 07 — 데이터베이스 연동 (SQLAlchemy)

## 학습 목표 (Goal)

SQLAlchemy 2.0과 FastAPI를 연동하여 SQLite 데이터베이스에 CRUD 작업을 수행하는 API를 구현합니다.

---

## 핵심 개념 (Core Concepts)

### SQLAlchemy 2.0의 구성 요소

```
FastAPI 엔드포인트
       │
       ▼
  Session (세션)              ← 데이터베이스와의 대화 단위
       │
       ▼
  ORM Model (모델)            ← Python 클래스 ↔ DB 테이블 매핑
       │
       ▼
  Engine (엔진)               ← 실제 DB 연결을 관리하는 커넥션 풀
       │
       ▼
  Database (SQLite/PostgreSQL)
```

![SQLAlchemy 아키텍처](images/07-sqlalchemy-architecture.png)
| 구성 요소 | 역할 |
|-----------|------|
| **Engine** | 데이터베이스 연결 문자열을 기반으로 커넥션 풀을 생성하고 관리 |
| **Session** | 하나의 요청(트랜잭션) 동안 DB 작업을 수행하는 단위. 커밋, 롤백 관리 |
| **ORM Model** | Python 클래스를 데이터베이스 테이블에 매핑. `Mapped` 타입 사용 (2.0 스타일) |
| **DeclarativeBase** | 모든 ORM 모델의 부모 클래스. 테이블 메타데이터를 관리 |

### Pydantic 모델 vs SQLAlchemy 모델

이 둘은 역할이 다릅니다:

| 구분 | Pydantic 모델 (schemas.py) | SQLAlchemy 모델 (models.py) |
|------|---------------------------|---------------------------|
| 역할 | 요청/응답 데이터 검증 및 직렬화 | 데이터베이스 테이블 구조 정의 |
| 위치 | API 계층 (HTTP 경계) | 데이터 계층 (DB 경계) |
| 예시 | `ItemCreate`, `ItemResponse` | `Item(Base)` |

---

## 실습 코드 (Hands-on)

이 실습에서는 다음 파일 구조를 사용합니다:

```text
my-fastapi-app/
├── main.py          ← 앱 진입점
├── database.py      ← DB 엔진, 세션 설정
├── models.py        ← SQLAlchemy ORM 모델
├── schemas.py       ← Pydantic 요청/응답 스키마
└── crud.py          ← CRUD 함수 (DB 작업 로직)
```

### Step 1: 데이터베이스 설정

**`database.py`**:

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

# SQLite 데이터베이스 (파일 기반)
# PostgreSQL 사용 시: "postgresql://user:password@host:5432/dbname"
DATABASE_URL = "sqlite:///./app.db"

# Engine 생성
# - echo=True: 실행되는 SQL을 콘솔에 출력 (디버깅용, 프로덕션에서는 False)
# - connect_args: SQLite는 기본적으로 단일 스레드이므로 다중 스레드 허용 설정
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},  # SQLite 전용 설정
)

# Session 팩토리
# - autocommit=False: 명시적으로 commit()을 호출해야 DB에 반영
# - autoflush=False: 쿼리 실행 전 자동 flush 방지 (명시적 제어)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# 모든 ORM 모델의 부모 클래스
class Base(DeclarativeBase):
    pass


# FastAPI 의존성으로 사용할 DB 세션 생성기
def get_db() -> Generator[Session, None, None]:
    """
    요청마다 새 세션을 생성하고, 응답 후 세션을 닫습니다.
    에러 발생 시에도 finally에서 세션이 닫힘을 보장합니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 2: ORM 모델 정의

**`models.py`**:

```python
# models.py
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from database import Base


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"

    # Mapped[type]과 mapped_column()으로 컬럼 정의 (SQLAlchemy 2.0 스타일)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # 관계 설정 — User 1:N Item
    items: Mapped[list["Item"]] = relationship(back_populates="owner")


class Item(Base):
    """아이템 테이블"""
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # 외래 키 — items.owner_id → users.id
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 관계 설정 — Item N:1 User
    owner: Mapped["User"] = relationship(back_populates="items")
```

### Step 3: Pydantic 스키마

**`schemas.py`**:

```python
# schemas.py
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


# --------------------------------------------------
# Item 스키마
# --------------------------------------------------
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(..., gt=0)


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --------------------------------------------------
# User 스키마
# --------------------------------------------------
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
    items: list[ItemResponse] = []  # 사용자의 아이템 목록 포함

    model_config = {"from_attributes": True}
```

### Step 4: CRUD 함수

**`crud.py`**:

```python
# crud.py
from sqlalchemy.orm import Session
from models import User, Item
from schemas import UserCreate, ItemCreate


# --------------------------------------------------
# User CRUD
# --------------------------------------------------
def get_user(db: Session, user_id: int) -> User | None:
    """사용자 단건 조회"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """이메일로 사용자 조회 (중복 확인용)"""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 10) -> list[User]:
    """사용자 목록 조회"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """사용자 생성"""
    # 실제로는 passlib 등으로 비밀번호 해시
    hashed_password = f"hashed_{user.password}"
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)       # 세션에 추가
    db.commit()           # DB에 반영
    db.refresh(db_user)   # DB에서 최신 상태 다시 읽기 (id, created_at 등)
    return db_user


# --------------------------------------------------
# Item CRUD
# --------------------------------------------------
def get_items(db: Session, skip: int = 0, limit: int = 10) -> list[Item]:
    """아이템 목록 조회"""
    return db.query(Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: ItemCreate, user_id: int) -> Item:
    """특정 사용자의 아이템 생성"""
    db_item = Item(**item.model_dump(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int) -> bool:
    """아이템 삭제"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        return False
    db.delete(db_item)
    db.commit()
    return True
```

### Step 5: 엔드포인트 연결

**`main.py`**:

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from database import engine, get_db, Base
from schemas import UserCreate, UserResponse, ItemCreate, ItemResponse
import crud

# 앱 시작 시 테이블 생성
# (프로덕션에서는 Alembic 마이그레이션 사용 권장)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Items API with DB")

# 의존성 타입 별칭
DbSession = Annotated[Session, Depends(get_db)]


# --------------------------------------------------
# User 엔드포인트
# --------------------------------------------------
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: DbSession):
    # 이메일 중복 검사
    existing = crud.get_user_by_email(db, email=user.email)
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    return crud.create_user(db=db, user=user)


@app.get("/users", response_model=list[UserResponse])
def list_users(db: DbSession, skip: int = 0, limit: int = 10):
    return crud.get_users(db, skip=skip, limit=limit)


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: DbSession):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return db_user


# --------------------------------------------------
# Item 엔드포인트
# --------------------------------------------------
@app.post("/users/{user_id}/items", response_model=ItemResponse, status_code=201)
def create_item_for_user(user_id: int, item: ItemCreate, db: DbSession):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items", response_model=list[ItemResponse])
def list_items(db: DbSession, skip: int = 0, limit: int = 10):
    return crud.get_items(db, skip=skip, limit=limit)


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, db: DbSession):
    success = crud.delete_item(db, item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
```

### Step 6: 실행 및 테스트

```bash
# 필요한 패키지가 모두 설치되었는지 확인
poetry install

# 서버 실행
poetry run uvicorn main:app --reload

# http://127.0.0.1:8000/docs 에서 Swagger UI로 테스트:
# 1. POST /users → 사용자 생성
# 2. POST /users/1/items → 아이템 생성
# 3. GET /users/1 → 사용자 정보 + 아이템 목록 확인
```

실행 시 `app.db` 파일이 프로젝트 루트에 생성됩니다. `echo=True` 설정에 의해 콘솔에서 실행되는 SQL 쿼리를 확인할 수 있습니다.

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- SQLAlchemy 2.0 엔진/세션 설정 (`database.py`)
- `Mapped`와 `mapped_column`을 사용한 ORM 모델 정의 (`models.py`)
- 요청/응답 스키마 분리 (`schemas.py`)
- CRUD 함수 분리 (`crud.py`)
- FastAPI 의존성 주입으로 DB 세션 관리

**다음 단계**: [08 — 인증과 JWT](08-authentication-jwt.md)에서 사용자 인증과 JWT 토큰 기반 접근 제어를 구현합니다.
