# 🧪 12 — 테스팅

## 학습 목표 (Goal)

FastAPI 앱을 `pytest`와 `TestClient(httpx)` 를 사용하여 체계적으로 테스트하는 방법을 학습합니다. 의존성 오버라이드를 통한 DB 격리 테스트 패턴을 포함합니다.

---

## 핵심 개념 (Core Concepts)

### 테스트 피라미드

```
        ╱╲
       ╱  ╲
      ╱ E2E ╲          ← 브라우저/통합 테스트 (느림, 적게)
     ╱────────╲
    ╱Integration╲       ← API 레벨 테스트 (이 문서의 주제)
   ╱──────────────╲
  ╱   Unit Tests    ╲   ← 개별 함수/클래스 테스트 (빠름, 많이)
 ╱────────────────────╲
```

FastAPI에서는 **Integration(통합) 테스트**가 가장 효과적입니다. `TestClient`를 사용하여 실제 HTTP 요청을 시뮬레이션하면, 라우팅, 검증, 의존성 주입, 응답 직렬화를 한 번에 검증할 수 있습니다.

### TestClient 동작 방식

```
TestClient (httpx 기반)
       │
       ▼  실제 HTTP를 보내지 않음 (in-process 호출)
  FastAPI ASGI 앱
       │
       ▼
  엔드포인트 함수 실행
       │
       ▼
  응답 반환 → TestClient가 수신
```

`TestClient`는 실제 네트워크를 사용하지 않고, 앱을 프로세스 내에서 직접 호출합니다. 따라서 서버를 별도로 실행할 필요가 없습니다.

---

## 실습 코드 (Hands-on)

### Step 1: 테스트 대상 앱

**`main.py`** (간단한 CRUD API):

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Annotated

app = FastAPI()

# 간단한 인메모리 저장소
items_db: dict[int, dict] = {}
next_id = 1


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float


def get_items_db():
    """DB 의존성 (테스트에서 오버라이드 가능)"""
    return items_db


ItemsDB = Annotated[dict, Depends(get_items_db)]


@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate, db: ItemsDB):
    global next_id
    item_data = {"id": next_id, **item.model_dump()}
    db[next_id] = item_data
    next_id += 1
    return item_data


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: ItemsDB):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]


@app.get("/items", response_model=list[ItemResponse])
def list_items(db: ItemsDB):
    return list(db.values())
```

### Step 2: 기본 테스트 작성

**`tests/test_items.py`**:

```python
# tests/test_items.py
import pytest
from fastapi.testclient import TestClient
from main import app, get_items_db

client = TestClient(app)


# --------------------------------------------------
# Fixture: 테스트마다 깨끗한 DB 상태 보장
# --------------------------------------------------
@pytest.fixture(autouse=True)
def clean_db():
    """
    각 테스트 실행 전에 DB를 비우고,
    의존성을 오버라이드하여 격리된 테스트 DB를 사용합니다.
    """
    test_db: dict[int, dict] = {}

    # 의존성 오버라이드: get_items_db → test_db 반환
    app.dependency_overrides[get_items_db] = lambda: test_db
    yield test_db
    # 테스트 후 오버라이드 초기화
    app.dependency_overrides.clear()


# --------------------------------------------------
# 아이템 생성 테스트
# --------------------------------------------------
class TestCreateItem:
    def test_create_item_success(self):
        """정상적인 아이템 생성"""
        response = client.post(
            "/items",
            json={"name": "노트북", "price": 1200000},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "노트북"
        assert data["price"] == 1200000
        assert "id" in data

    def test_create_item_invalid_name(self):
        """빈 이름으로 생성 시 422 에러"""
        response = client.post(
            "/items",
            json={"name": "", "price": 1000},
        )
        assert response.status_code == 422

    def test_create_item_negative_price(self):
        """음수 가격으로 생성 시 422 에러"""
        response = client.post(
            "/items",
            json={"name": "테스트", "price": -100},
        )
        assert response.status_code == 422

    def test_create_item_missing_fields(self):
        """필수 필드 누락 시 422 에러"""
        response = client.post("/items", json={})
        assert response.status_code == 422


# --------------------------------------------------
# 아이템 조회 테스트
# --------------------------------------------------
class TestGetItem:
    def test_get_item_success(self, clean_db):
        """존재하는 아이템 조회"""
        # 먼저 아이템 생성
        create_response = client.post(
            "/items",
            json={"name": "마우스", "price": 35000},
        )
        item_id = create_response.json()["id"]

        # 생성된 아이템 조회
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "마우스"

    def test_get_item_not_found(self):
        """존재하지 않는 아이템 조회 시 404 에러"""
        response = client.get("/items/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Item not found"


# --------------------------------------------------
# 아이템 목록 조회 테스트
# --------------------------------------------------
class TestListItems:
    def test_list_items_empty(self):
        """빈 목록 조회"""
        response = client.get("/items")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_items_after_creation(self):
        """아이템 생성 후 목록 확인"""
        client.post("/items", json={"name": "아이템1", "price": 1000})
        client.post("/items", json={"name": "아이템2", "price": 2000})

        response = client.get("/items")
        assert response.status_code == 200
        assert len(response.json()) == 2
```

### Step 3: 테스트 실행

```bash
# 테스트 실행
poetry run pytest tests/ -v

# 출력 예시:
# tests/test_items.py::TestCreateItem::test_create_item_success PASSED
# tests/test_items.py::TestCreateItem::test_create_item_invalid_name PASSED
# tests/test_items.py::TestCreateItem::test_create_item_negative_price PASSED
# tests/test_items.py::TestCreateItem::test_create_item_missing_fields PASSED
# tests/test_items.py::TestGetItem::test_get_item_success PASSED
# tests/test_items.py::TestGetItem::test_get_item_not_found PASSED
# tests/test_items.py::TestListItems::test_list_items_empty PASSED
# tests/test_items.py::TestListItems::test_list_items_after_creation PASSED

# 커버리지 포함 실행
poetry run pytest tests/ -v --cov=. --cov-report=term-missing
```

### Step 4: 비동기 테스트 (httpx AsyncClient)

비동기 엔드포인트를 테스트하려면 `httpx.AsyncClient`를 사용합니다:

```python
# tests/test_async.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.anyio
async def test_root():
    """비동기 테스트 — httpx AsyncClient 사용"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        # 엔드포인트가 정의되어 있지 않으면 404
        assert response.status_code in (200, 404)
```

### Step 5: conftest.py로 Fixture 공유

**`tests/conftest.py`**:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """여러 테스트 파일에서 공유할 TestClient"""
    with TestClient(app) as c:
        yield c
```

---

## 테스트 작성 권장 사항

| 항목 | 권장 사항 |
|------|-----------|
| 테스트 명명 | `test_<대상>_<상황>` (예: `test_create_item_success`) |
| 의존성 격리 | `dependency_overrides`로 DB, 외부 서비스 교체 |
| 상태 초기화 | fixture의 `autouse=True`로 매 테스트 전 DB 초기화 |
| 검증 항목 | 상태 코드, 응답 본문, 에러 메시지 모두 검증 |
| 경계값 테스트 | 빈 문자열, 0, 음수, 최대값 등 경계 조건 포함 |

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- `TestClient`를 사용한 통합 테스트 작성
- `dependency_overrides`를 통한 의존성 격리
- `pytest.fixture`로 테스트 상태 관리
- 정상/에러/검증 실패 케이스 테스트
- 비동기 테스트 패턴 (`httpx.AsyncClient`)

**다음 단계**: [13 — 비동기 처리와 성능](13-async-and-performance.md)에서 FastAPI의 비동기 동작 원리와 성능 최적화 기법을 학습합니다.
