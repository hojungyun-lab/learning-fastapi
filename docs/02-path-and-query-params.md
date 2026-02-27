# 📍 02 — 경로와 쿼리 파라미터

## 학습 목표 (Goal)

URL에서 데이터를 추출하는 두 가지 방법(경로 파라미터, 쿼리 파라미터)을 이해하고, FastAPI의 자동 타입 변환과 검증(validation) 기능을 활용하는 방법을 학습합니다.

---

## 핵심 개념 (Core Concepts)

### 경로 파라미터 vs 쿼리 파라미터

```
GET /users/42?role=admin&active=true
     ──────  ────────────────────────
        │               │
   경로 파라미터      쿼리 파라미터
   (Path Parameter)  (Query Parameter)
```

| 구분 | 경로 파라미터 | 쿼리 파라미터 |
|------|---------------|---------------|
| 위치 | URL 경로 내부 (`/users/{id}`) | `?` 뒤의 key=value 쌍 |
| 용도 | 특정 리소스 식별 | 필터링, 정렬, 페이지네이션 등 |
| 필수 여부 | 항상 필수 | 기본값을 설정하면 선택적 |
| 예시 | `/items/42` | `/items?skip=0&limit=10` |

### FastAPI의 자동 처리

FastAPI는 함수 시그니처(파라미터의 이름과 타입 힌트)를 분석하여 다음을 자동으로 수행합니다:

1. **소스 판별**: 파라미터 이름이 경로 템플릿 `{}`에 있으면 경로 파라미터, 없으면 쿼리 파라미터로 인식
2. **타입 변환**: 문자열로 전달된 URL 값을 타입 힌트에 따라 `int`, `float`, `bool` 등으로 자동 변환
3. **검증 오류 응답**: 변환 실패 시 422 Unprocessable Entity 응답을 자동 생성 (요청 실패 이유를 JSON으로 반환)

---

## 실습 코드 (Hands-on)

### Step 1: 경로 파라미터

**`main.py`** 파일을 작성합니다:

```python
# main.py
from fastapi import FastAPI

app = FastAPI()


# --------------------------------------------------
# 기본 경로 파라미터 — 타입 힌트로 자동 변환
# --------------------------------------------------
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    user_id는 URL 경로에서 추출됩니다.
    - GET /users/42  → user_id = 42 (int)
    - GET /users/abc → 422 에러 (int로 변환 불가)
    """
    return {"user_id": user_id}


# --------------------------------------------------
# 여러 경로 파라미터 조합
# --------------------------------------------------
@app.get("/organizations/{org_id}/members/{member_id}")
def get_org_member(org_id: int, member_id: int):
    """URL 내 여러 경로 파라미터를 동시에 사용"""
    return {"org_id": org_id, "member_id": member_id}


# --------------------------------------------------
# 주의: 라우트 순서가 중요합니다
# --------------------------------------------------

# "/users/me"를 먼저 정의해야 합니다.
# 만약 "/users/{user_id}"가 먼저 있으면, "me"를 user_id로 인식합니다.
@app.get("/users/me")
def get_current_user():
    """현재 사용자 정보 (고정 경로)"""
    return {"user": "current_user"}


# 아래 라우트는 "/users/me" 이후에 정의
@app.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    """특정 사용자 조회 (동적 경로)"""
    return {"user_id": user_id}
```

> **참고**: 위 코드에서 `get_user`와 `get_user_by_id`는 동일한 경로 패턴입니다. 실제 프로젝트에서는 하나만 남기면 됩니다. 여기서는 라우트 순서의 중요성을 설명하기 위해 작성했습니다.

### Step 2: 쿼리 파라미터

```python
# main.py (이어서 추가)

# --------------------------------------------------
# 기본 쿼리 파라미터 — 기본값이 있으면 선택적
# --------------------------------------------------
@app.get("/items")
def list_items(skip: int = 0, limit: int = 10):
    """
    GET /items          → skip=0, limit=10 (기본값)
    GET /items?skip=5   → skip=5, limit=10
    GET /items?limit=20 → skip=0, limit=20
    """
    # 실제로는 DB 쿼리에 offset/limit을 적용
    fake_items = [{"id": i, "name": f"Item {i}"} for i in range(100)]
    return fake_items[skip : skip + limit]


# --------------------------------------------------
# 선택적 쿼리 파라미터 — None 허용
# --------------------------------------------------
@app.get("/search")
def search_items(q: str | None = None, category: str | None = None):
    """
    GET /search                    → q=None, category=None
    GET /search?q=노트북           → q="노트북", category=None
    GET /search?q=노트북&category=전자 → q="노트북", category="전자"
    """
    results = {"query": q, "category": category}
    return results


# --------------------------------------------------
# 필수 쿼리 파라미터 — 기본값이 없으면 필수
# --------------------------------------------------
@app.get("/convert")
def convert_currency(amount: float, from_currency: str, to_currency: str):
    """
    GET /convert?amount=100&from_currency=USD&to_currency=KRW
    → 세 파라미터 모두 필수. 하나라도 빠지면 422 에러
    """
    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
    }
```

### Step 3: Path와 Query를 사용한 고급 검증

`Path`와 `Query`는 경로/쿼리 파라미터에 검증 규칙, 설명, 예시값을 추가하는 기능입니다.

```python
# main.py (이어서 추가)
from fastapi import Path, Query


@app.get("/products/{product_id}")
def get_product(
    # Path: 경로 파라미터에 검증 규칙 추가
    product_id: int = Path(
        ...,                          # ... 은 필수를 의미
        ge=1,                         # 1 이상 (greater than or equal)
        le=10000,                     # 10000 이하 (less than or equal)
        description="제품 고유 ID",
        examples=[42],
    ),
    # Query: 쿼리 파라미터에 검증 규칙 추가
    fields: str | None = Query(
        None,                         # 기본값 None (선택적)
        min_length=1,                 # 최소 길이
        max_length=200,               # 최대 길이
        pattern=r"^[a-z,]+$",         # 정규표현식 패턴 (소문자 + 콤마만 허용)
        description="응답에 포함할 필드 (콤마 구분)",
        examples=["name,price"],
    ),
):
    """
    검증 규칙이 적용된 엔드포인트:
    - GET /products/0           → 422 에러 (ge=1 위반)
    - GET /products/42          → 정상
    - GET /products/42?fields=name,price → 정상
    - GET /products/42?fields=NAME → 422 에러 (pattern 위반)
    """
    result = {"product_id": product_id}
    if fields:
        result["fields"] = fields.split(",")
    return result
```

### Step 4: Enum을 활용한 경로 파라미터 제한

특정 값만 허용해야 하는 경우 `Enum`을 사용합니다:

```python
# main.py (이어서 추가)
from enum import Enum


class SortOrder(str, Enum):
    """허용되는 정렬 순서를 Enum으로 정의"""
    asc = "asc"
    desc = "desc"


class Category(str, Enum):
    """허용되는 카테고리 목록"""
    electronics = "electronics"
    books = "books"
    clothing = "clothing"


@app.get("/categories/{category}/items")
def list_category_items(
    category: Category,              # Enum에 정의된 값만 허용
    sort: SortOrder = SortOrder.asc, # 기본값: asc
):
    """
    - GET /categories/electronics/items       → 정상
    - GET /categories/food/items              → 422 에러 (Enum에 없음)
    
    Swagger UI에서 category, sort가 드롭다운으로 표시됨
    """
    return {
        "category": category.value,
        "sort": sort.value,
    }
```

---

## 검증 에러 응답 예시

잘못된 요청을 보내면 FastAPI가 자동으로 생성하는 422 에러 응답:

```json
// GET /products/0 (ge=1 위반)
{
    "detail": [
        {
            "type": "greater_than_equal",
            "loc": ["path", "product_id"],
            "msg": "Input should be greater than or equal to 1",
            "input": "0",
            "ctx": {"ge": 1}
        }
    ]
}
```

- `loc`: 에러가 발생한 위치 (`path` 또는 `query`)와 파라미터 이름
- `msg`: 검증 실패 사유
- `ctx`: 적용된 검증 규칙

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- 경로 파라미터와 쿼리 파라미터의 차이점과 사용법
- FastAPI의 자동 타입 변환과 검증 기능
- `Path`, `Query`를 사용한 고급 검증 규칙 지정
- `Enum`을 활용한 허용 값 제한

지금까지는 URL과 쿼리 스트링에서 단순한 값을 추출했습니다. **다음 단계**: [03 — 요청 본문과 Pydantic](03-request-body-and-pydantic.md)에서 JSON 요청 본문을 Pydantic 모델로 파싱하고 검증하는 방법을 학습합니다.
