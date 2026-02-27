# ⚠️ 09 — 에러 핸들링

## 학습 목표 (Goal)

FastAPI에서 에러를 체계적으로 관리하는 방법을 학습합니다. HTTPException, 커스텀 예외, 전역 에러 핸들러를 사용하여 일관된 에러 응답 구조를 구현합니다.

---

## 핵심 개념 (Core Concepts)

### FastAPI의 에러 처리 계층

```
요청 수신
   │
   ▼
미들웨어 체인
   │
   ▼
라우트 매칭 실패 ──→ 404 자동 응답
   │
   ▼
Pydantic 검증 실패 ──→ 422 자동 응답 (RequestValidationError)
   │
   ▼
엔드포인트 함수 실행
   ├── raise HTTPException ──→ 지정된 상태 코드 + detail
   ├── raise CustomException ──→ 등록된 exception_handler 호출
   └── 예상치 못한 에러 ──→ 500 Internal Server Error
```

### 에러 사용 기준

| 상황 | 방법 |
|------|------|
| 단순한 HTTP 에러 (404, 403 등) | `HTTPException` |
| 도메인 규칙 위반 (재고 부족, 중복 등) | 커스텀 예외 클래스 + `exception_handler` |
| 검증 에러 형식 변경 | `RequestValidationError` 핸들러 재정의 |
| 모든 예외에 대한 로깅 | 전역 `Exception` 핸들러 |

---

## 실습 코드 (Hands-on)

### Step 1: HTTPException 기본 사용

```python
# main.py
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

items_db = {1: {"id": 1, "name": "노트북", "price": 1200000}}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in items_db:
        # HTTPException: 가장 기본적인 에러 응답 방법
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="아이템을 찾을 수 없습니다",
            # 선택적: 응답 헤더 추가
            headers={"X-Error-Code": "ITEM_NOT_FOUND"},
        )
    return items_db[item_id]


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    # 삭제 조건 검증
    item = items_db[item_id]
    if item.get("is_locked"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="잠금 상태인 아이템은 삭제할 수 없습니다",
        )

    del items_db[item_id]
```

### Step 2: 커스텀 예외 클래스와 핸들러

도메인 로직의 예외를 별도 클래스로 정의하면, 비즈니스 로직과 HTTP 응답을 분리할 수 있습니다:

```python
# exceptions.py
class AppException(Exception):
    """앱 전체 예외의 기본 클래스"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code


class ItemNotFoundError(AppException):
    """아이템을 찾을 수 없을 때"""
    def __init__(self, item_id: int):
        super().__init__(
            message=f"아이템(ID: {item_id})을 찾을 수 없습니다",
            code="ITEM_NOT_FOUND",
        )
        self.item_id = item_id


class DuplicateEmailError(AppException):
    """이메일 중복 시"""
    def __init__(self, email: str):
        super().__init__(
            message=f"이미 등록된 이메일입니다: {email}",
            code="DUPLICATE_EMAIL",
        )


class InsufficientStockError(AppException):
    """재고 부족 시"""
    def __init__(self, item_id: int, requested: int, available: int):
        super().__init__(
            message=f"재고 부족: 요청 {requested}개, 잔여 {available}개",
            code="INSUFFICIENT_STOCK",
        )
```

```python
# main.py (이어서 추가)
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from exceptions import AppException, ItemNotFoundError, InsufficientStockError


# --------------------------------------------------
# 커스텀 예외 핸들러 등록
# --------------------------------------------------
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    AppException과 그 하위 클래스를 모두 처리합니다.
    일관된 에러 응답 구조를 보장합니다.
    """
    # 예외 타입에 따라 상태 코드 매핑
    status_map = {
        "ITEM_NOT_FOUND": 404,
        "DUPLICATE_EMAIL": 409,
        "INSUFFICIENT_STOCK": 400,
    }
    status_code = status_map.get(exc.code, 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


# 사용 예시
@app.get("/products/{product_id}")
def get_product(product_id: int):
    # HTTPException 대신 도메인 예외를 사용
    raise ItemNotFoundError(item_id=product_id)


@app.post("/orders")
def create_order():
    raise InsufficientStockError(item_id=1, requested=10, available=3)
```

에러 응답 예시:

```json
{
    "error": {
        "code": "ITEM_NOT_FOUND",
        "message": "아이템(ID: 42)을 찾을 수 없습니다"
    }
}
```

### Step 3: Pydantic 검증 에러 커스터마이징

FastAPI의 기본 422 에러 응답 형식을 변경합니다:

```python
# main.py (이어서 추가)
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Pydantic 검증 실패 시 응답 형식 커스터마이징.
    기본 422 응답을 앱의 에러 형식에 맞춰 변환합니다.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "요청 데이터 검증에 실패했습니다",
                "details": errors,
            }
        },
    )
```

커스터마이징된 검증 에러 응답:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "요청 데이터 검증에 실패했습니다",
        "details": [
            {
                "field": "body → price",
                "message": "Input should be greater than 0",
                "type": "greater_than"
            }
        ]
    }
}
```

### Step 4: 전역 예외 핸들러 (로깅)

예상치 못한 에러를 잡아 500 응답을 반환하고, 에러를 로깅합니다:

```python
# main.py (이어서 추가)
import logging

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    모든 미처리 예외를 잡아 500 응답을 반환합니다.
    프로덕션에서는 에러 내용을 클라이언트에 노출하지 않습니다.
    """
    logger.error(
        f"Unhandled error: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
            }
        },
    )
```

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- `HTTPException`을 사용한 기본 에러 응답
- 커스텀 예외 클래스와 `exception_handler`로 도메인 에러 분리
- `RequestValidationError` 핸들러 재정의로 검증 에러 형식 통일
- 전역 예외 핸들러로 미처리 에러 대응 및 로깅

**다음 단계**: [10 — 미들웨어와 CORS](10-middleware-and-cors.md)에서 요청/응답 처리 파이프라인에 공통 로직을 삽입하는 미들웨어를 학습합니다.
