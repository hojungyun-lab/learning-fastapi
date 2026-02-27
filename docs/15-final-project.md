# 🏆 15 — 실전 프로젝트 가이드

## 학습 목표 (Goal)

지금까지 학습한 FastAPI의 모든 기능을 통합하여 **Todo API**를 구현합니다. 이 문서에서는 `examples/final-project/`의 전체 아키텍처와 구현 패턴을 설명합니다.

---

## 프로젝트 아키텍처

### 디렉터리 구조

```text
final-project/
├── app/
│   ├── __init__.py
│   ├── main.py              ← 앱 진입점, lifespan, 라우터 등록
│   ├── config.py            ← 환경 변수 설정 (pydantic-settings)
│   ├── database.py          ← DB 엔진, 세션, Base 클래스
│   ├── models.py            ← SQLAlchemy ORM 모델
│   ├── schemas.py           ← Pydantic 요청/응답 스키마
│   ├── auth.py              ← JWT 인증 로직
│   ├── dependencies.py      ← 공통 의존성 (DB 세션, 현재 사용자)
│   ├── exceptions.py        ← 커스텀 예외
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          ← 회원가입, 로그인 엔드포인트
│       └── todos.py         ← Todo CRUD 엔드포인트
├── tests/
│   ├── __init__.py
│   ├── conftest.py          ← 테스트 Fixture
│   ├── test_auth.py         ← 인증 테스트
│   └── test_todos.py        ← Todo CRUD 테스트
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

### 계층 간 데이터 흐름

```
HTTP 요청
    │
    ▼
Router (routers/*.py)         ← URL 라우팅, 요청/응답 정의
    │
    ├── Schemas (schemas.py)  ← 요청 검증, 응답 직렬화
    ├── Dependencies          ← DB 세션, 인증, 페이지네이션
    │
    ▼
Models (models.py)            ← SQLAlchemy ORM, DB 작업
    │
    ▼
Database (database.py)        ← 세션 관리, 엔진
```

---

## 구현 패턴 요약

이 프로젝트에서 적용한 패턴을 학습 문서별로 정리합니다:

| 학습 문서 | 적용 위치 | 패턴 |
|----------|-----------|------|
| 01 라우팅 | `routers/` | APIRouter로 모듈 분리 |
| 02 파라미터 | `routers/todos.py` | Query로 필터/페이지네이션 |
| 03 Pydantic | `schemas.py` | 요청/응답 스키마 분리, 검증 |
| 04 응답 | `routers/` | response_model, status_code |
| 06 의존성 주입 | `dependencies.py` | Annotated + Depends 활용 |
| 07 데이터베이스 | `models.py`, `database.py` | SQLAlchemy 2.0 Mapped 스타일 |
| 08 인증 | `auth.py`, `routers/auth.py` | JWT + OAuth2PasswordBearer |
| 09 에러 핸들링 | `exceptions.py` | 커스텀 예외 + 전역 핸들러 |
| 10 미들웨어 | `main.py` | CORS, 처리 시간 측정 |
| 12 테스팅 | `tests/` | dependency_overrides, Fixture |
| 13 비동기 | `main.py` | lifespan 리소스 관리 |
| 14 배포 | `Dockerfile` | 멀티 스테이지 빌드 |

---

## API 명세

### 인증

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/auth/register` | 회원가입 |
| POST | `/auth/token` | 로그인 (JWT 토큰 발급) |
| GET | `/auth/me` | 현재 사용자 정보 |

### Todo

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/todos` | Todo 목록 조회 (필터, 페이지네이션) |
| POST | `/todos` | Todo 생성 |
| GET | `/todos/{id}` | Todo 단건 조회 |
| PATCH | `/todos/{id}` | Todo 부분 수정 |
| DELETE | `/todos/{id}` | Todo 삭제 |

### 필터 및 페이지네이션

```
GET /todos?completed=false&skip=0&limit=10&search=회의
```

---

## 실행 방법

### 로컬 개발 환경

```bash
# final-project 디렉터리로 이동
cd examples/final-project

# 의존성 설치
poetry install

# 환경 변수 설정
cp .env.example .env

# 서버 실행
poetry run uvicorn app.main:app --reload

# 테스트 실행
poetry run pytest tests/ -v
```

### Docker 환경

```bash
cd examples/final-project

# docker-compose로 앱 + DB 시작
docker compose up -d

# http://localhost:8000/docs 에서 API 문서 확인
```

---

## 학습 완료 후 확장 아이디어

실전 프로젝트를 더 발전시키려면 다음 기능을 추가해 보세요:

| 기능 | 관련 기술 |
|------|-----------|
| Todo 카테고리/태그 | SQLAlchemy 다대다 관계 |
| 마감일 알림 | BackgroundTasks + 스케줄러 |
| 사용자별 할당량 제한 | 미들웨어 Rate Limiting |
| 파일 첨부 | UploadFile + 스토리지 서비스 |
| WebSocket 실시간 알림 | FastAPI WebSocket |
| Alembic 마이그레이션 | 스키마 버전 관리 |
| CI/CD 파이프라인 | GitHub Actions + Docker |
| Redis 캐싱 | 조회 성능 최적화 |

---

## 마무리

이 학습 가이드의 16개 문서를 통해 다음을 달성했습니다:

- FastAPI의 핵심 기능 (라우팅, Pydantic, DI, 인증, DB, 테스팅)을 실습
- 프로덕션 수준의 코드 구조와 패턴 적용
- Docker 기반 배포 환경 구성

`examples/final-project/` 코드를 기반으로 다양한 기능을 확장하면서 학습을 이어가기를 권장합니다.
