# 🚀 FastAPI 완전 정복 — 실전 학습 가이드

> **FastAPI**를 처음 접하는 개발자가 환경 설정부터 프로덕션 배포까지, 단계별로 학습할 수 있는 종합 가이드북입니다.

## 이 가이드의 특징

- **16단계 커리큘럼**: 환경 설정 → 핵심 기능 → 인증/DB → 배포까지 순서대로 학습
- **현업 기준 코드**: 모든 예제는 FastAPI 0.133.x, Pydantic v2, SQLAlchemy 2.0 기반
- **바로 실행 가능**: `examples/` 디렉터리의 완성된 프로젝트를 즉시 구동 가능
- **Poetry 기반**: 의존성 관리를 Poetry로 통일하여 재현 가능한 환경 제공

---

## 📁 프로젝트 구조

```text
.
├── README.md               ← 지금 보고 있는 문서
├── CHEATSHEET.md            ← 핵심 문법/패턴 빠른 참조 카드
├── pyproject.toml           ← Poetry 프로젝트 설정
├── docs/                    ← 단계별 학습 문서 (00 ~ 15)
│   ├── 00-environment-setup.md
│   ├── 01-hello-fastapi.md
│   ├── 02-path-and-query-params.md
│   ├── ...
│   └── 15-final-project.md
└── examples/                ← 완성된 데모 코드
    ├── basic-app/           ← 기초 단계 통합 데모 (CRUD API)
    └── final-project/       ← 심화 실전 완성형 앱 (Todo API)
```

---

## 🚀 시작하기

### 1. 사전 요구사항 확인

```bash
# Python 3.11 이상 확인
python3 --version

# Poetry 설치 확인 (미설치 시: https://python-poetry.org/docs/#installation)
poetry --version
```

### 2. 학습용 빈 프로젝트 생성

직접 코드를 따라 치며 학습하려면, 별도의 디렉터리에서 새 프로젝트를 만듭니다.

```bash
# 학습용 디렉터리 생성
mkdir my-fastapi-practice && cd my-fastapi-practice

# Poetry 프로젝트 초기화
poetry init --name my-fastapi-practice --python "^3.11" --no-interaction

# FastAPI 및 Uvicorn 설치
poetry add fastapi "uvicorn[standard]"

# 가상환경 활성화
poetry shell
```

### 3. 완성된 예제 코드 실행

이 레포지토리의 예제 코드를 직접 실행해 보려면:

```bash
# 레포지토리 클론
git clone https://github.com/hojungyun-lab/learning-fastapi.git
cd learning-fastapi

# 의존성 설치
poetry install

# 기초 예제 실행
cd examples/basic-app
poetry run uvicorn main:app --reload
# → http://127.0.0.1:8000/docs 에서 Swagger UI 확인

# 실전 프로젝트 실행
cd ../final-project
poetry run uvicorn app.main:app --reload
# → http://127.0.0.1:8000/docs 에서 Swagger UI 확인
```

---

## 📚 학습 목차 (커리큘럼)

### 기초 단계 — FastAPI 입문

| # | 주제 | 핵심 내용 |
|---|------|----------|
| 00 | [개발 환경 구성](docs/00-environment-setup.md) | Python, Poetry, VS Code, 프로젝트 초기화 |
| 01 | [첫 번째 API 서버](docs/01-hello-fastapi.md) | FastAPI 인스턴스, 라우트 정의, Uvicorn 실행 |
| 02 | [경로와 쿼리 파라미터](docs/02-path-and-query-params.md) | URL 파싱, 타입 변환, 자동 검증 |
| 03 | [요청 본문과 Pydantic](docs/03-request-body-and-pydantic.md) | BaseModel, Field, 중첩 모델, 데이터 검증 |
| 04 | [응답 모델과 상태 코드](docs/04-response-model-and-status.md) | response_model, status_code, 필드 필터링 |
| 05 | [폼 데이터와 파일 업로드](docs/05-form-and-file-upload.md) | Form, File, UploadFile, 멀티파트 처리 |

### 프레임워크 핵심 — 아키텍처와 데이터

| # | 주제 | 핵심 내용 |
|---|------|----------|
| 06 | [의존성 주입](docs/06-dependency-injection.md) | Depends, yield 의존성, 계층화 패턴 |
| 07 | [데이터베이스 연동](docs/07-database-sqlalchemy.md) | SQLAlchemy 2.0, 세션 관리, CRUD 패턴 |
| 08 | [인증과 JWT](docs/08-authentication-jwt.md) | OAuth2PasswordBearer, JWT 발급/검증 |
| 09 | [에러 핸들링](docs/09-error-handling.md) | HTTPException, 커스텀 핸들러, 에러 구조화 |
| 10 | [미들웨어와 CORS](docs/10-middleware-and-cors.md) | 요청/응답 미들웨어, CORS 설정 |

### 고급 & 실전 — 배포와 프로젝트

| # | 주제 | 핵심 내용 |
|---|------|----------|
| 11 | [백그라운드 태스크](docs/11-background-tasks.md) | BackgroundTasks, 비동기 작업 분리 |
| 12 | [테스팅](docs/12-testing.md) | TestClient, pytest, DB 테스트 패턴 |
| 13 | [비동기 처리와 성능](docs/13-async-and-performance.md) | async/await 동작 원리, 동시성 모델 |
| 14 | [배포](docs/14-deployment.md) | Dockerfile, docker-compose, Uvicorn 설정 |
| 15 | [실전 프로젝트](docs/15-final-project.md) | 전체 아키텍처 통합, 실전 앱 구현 |

---

## 📋 빠른 참조

핵심 문법과 패턴을 빠르게 확인하려면 **[CHEATSHEET.md](CHEATSHEET.md)** 를 참고하세요.

---

## 기술 스택

| 항목 | 버전 | 용도 |
|------|------|------|
| FastAPI | 0.133.x | 웹 프레임워크 |
| Python | 3.11+ | 런타임 |
| Poetry | 2.x | 패키지 관리 |
| Pydantic | v2 | 데이터 검증/직렬화 |
| SQLAlchemy | 2.0 | ORM / 데이터베이스 |
| Uvicorn | 0.34.x | ASGI 서버 |
| pytest + httpx | 최신 | 테스트 |
| Docker | 최신 | 컨테이너 배포 |

---

## 라이선스

이 학습 자료는 MIT 라이선스로 제공됩니다. 자유롭게 활용하세요.
