# 🌐 01 — 첫 번째 API 서버

## 학습 목표 (Goal)

FastAPI 앱의 구조를 이해하고, 다양한 HTTP 메서드(GET, POST, PUT, DELETE)를 사용하여 기본적인 CRUD API를 구성하는 방법을 학습합니다.

---

## 핵심 개념 (Core Concepts)

### FastAPI 앱의 동작 흐름

FastAPI 앱을 실행하면 내부적으로 다음 과정이 진행됩니다:

1. **앱 인스턴스 생성**: `FastAPI()` 호출 시 Starlette 기반의 ASGI 앱 객체가 생성됩니다.
2. **라우트 등록**: `@app.get()`, `@app.post()` 등의 데코레이터로 URL 패턴과 핸들러 함수를 매핑합니다.
3. **OpenAPI 스키마 생성**: 등록된 라우트의 타입 힌트를 분석하여 OpenAPI(Swagger) 문서를 자동 생성합니다.
4. **요청 처리**: Uvicorn이 HTTP 요청을 수신하면, 등록된 라우트에서 URL이 일치하는 핸들러 함수를 호출합니다.

### HTTP 메서드와 CRUD

REST API에서 HTTP 메서드는 리소스에 대한 작업 유형을 나타냅니다:

| HTTP 메서드 | 작업 | 설명 |
|-------------|------|------|
| `GET` | Read | 리소스 조회 (목록 또는 단건) |
| `POST` | Create | 새 리소스 생성 |
| `PUT` | Update | 리소스 전체 수정 |
| `PATCH` | Partial Update | 리소스 부분 수정 |
| `DELETE` | Delete | 리소스 삭제 |

### APIRouter — 라우트 분리

프로젝트 규모가 커지면, 모든 엔드포인트를 `main.py`에 작성하는 것은 유지 보수에 문제가 됩니다. `APIRouter`를 사용하면 라우트를 모듈별로 분리할 수 있습니다.

```
main.py
  ├── app.include_router(items_router)
  └── app.include_router(users_router)

routers/
  ├── items.py   → APIRouter(prefix="/items")
  └── users.py   → APIRouter(prefix="/users")
```

---

## 실습 코드 (Hands-on)

### Step 1: 기본 CRUD API 작성

**`main.py`** 파일을 다음과 같이 작성합니다:

```python
# main.py
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Items API",
    description="FastAPI 학습용 기본 CRUD API",
    version="0.1.0",
)

# --------------------------------------------------
# 임시 데이터 저장소 (데이터베이스 대신 딕셔너리 사용)
# --------------------------------------------------
items_db: dict[int, dict] = {
    1: {"id": 1, "name": "노트북", "price": 1200000},
    2: {"id": 2, "name": "마우스", "price": 35000},
}
next_id = 3  # 다음 아이템 ID


# --------------------------------------------------
# GET — 리소스 조회
# --------------------------------------------------
@app.get("/")
def root():
    """API 루트 엔드포인트"""
    return {"message": "Items API is running"}


@app.get("/items")
def list_items():
    """전체 아이템 목록 조회"""
    return list(items_db.values())


@app.get("/items/{item_id}")
def get_item(item_id: int):
    """단건 아이템 조회 — item_id는 URL 경로에서 추출"""
    if item_id not in items_db:
        # 404 Not Found 응답
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


# --------------------------------------------------
# POST — 리소스 생성
# --------------------------------------------------
@app.post("/items", status_code=201)
def create_item(name: str, price: float):
    """새 아이템 생성 — status_code=201로 '생성됨' 응답"""
    global next_id
    item = {"id": next_id, "name": name, "price": price}
    items_db[next_id] = item
    next_id += 1
    return item


# --------------------------------------------------
# PUT — 리소스 전체 수정
# --------------------------------------------------
@app.put("/items/{item_id}")
def update_item(item_id: int, name: str, price: float):
    """아이템 전체 수정"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id] = {"id": item_id, "name": name, "price": price}
    return items_db[item_id]


# --------------------------------------------------
# DELETE — 리소스 삭제
# --------------------------------------------------
@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    """아이템 삭제 — status_code=204는 '내용 없음' (삭제 성공)"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    # 204 응답은 본문(body)이 없음
```

### Step 2: 서버 실행 및 테스트

```bash
poetry run uvicorn main:app --reload
```

http://127.0.0.1:8000/docs 에서 Swagger UI를 열고, 각 엔드포인트를 직접 테스트합니다:

1. `GET /items` — 전체 목록 조회
2. `POST /items` — `name=키보드`, `price=89000`으로 새 아이템 생성
3. `GET /items/3` — 방금 생성한 아이템 조회
4. `PUT /items/3` — 이름을 `기계식 키보드`, 가격을 `129000`으로 수정
5. `DELETE /items/3` — 아이템 삭제

### Step 3: APIRouter로 라우트 분리

프로젝트가 커지면 라우트를 파일별로 분리합니다. 다음 구조로 변경합니다:

```text
my-fastapi-app/
├── main.py
└── routers/
    └── items.py
```

**`routers/items.py`** — 아이템 관련 라우트를 분리:

```python
# routers/items.py
from fastapi import APIRouter, HTTPException

# prefix: 이 라우터의 모든 경로 앞에 /items가 붙음
# tags: Swagger UI에서 그룹으로 표시
router = APIRouter(prefix="/items", tags=["Items"])

items_db: dict[int, dict] = {
    1: {"id": 1, "name": "노트북", "price": 1200000},
    2: {"id": 2, "name": "마우스", "price": 35000},
}
next_id = 3


@router.get("/")
def list_items():
    """전체 아이템 목록 조회"""
    return list(items_db.values())


@router.get("/{item_id}")
def get_item(item_id: int):
    """단건 아이템 조회"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@router.post("/", status_code=201)
def create_item(name: str, price: float):
    """새 아이템 생성"""
    global next_id
    item = {"id": next_id, "name": name, "price": price}
    items_db[next_id] = item
    next_id += 1
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int):
    """아이템 삭제"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
```

**`main.py`** — 라우터 등록:

```python
# main.py
from fastapi import FastAPI
from routers.items import router as items_router

app = FastAPI(title="Items API", version="0.1.0")

# 라우터 등록 — items_router의 모든 경로가 앱에 추가됨
app.include_router(items_router)


@app.get("/")
def root():
    return {"message": "Items API is running"}
```

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- FastAPI 앱 인스턴스 생성 및 설정 옵션 이해
- GET, POST, PUT, DELETE 엔드포인트 작성
- Swagger UI에서 API 테스트
- `APIRouter`를 사용한 라우트 모듈 분리

현재까지의 API는 파라미터를 쿼리 스트링으로만 받고 있습니다. **다음 단계**: [02 — 경로와 쿼리 파라미터](02-path-and-query-params.md)에서 URL 경로와 쿼리 파라미터를 체계적으로 다루는 방법을 학습합니다.
