# 📦 03 — 요청 본문과 Pydantic

## 학습 목표 (Goal)

JSON 형식의 요청 본문(Request Body)을 Pydantic 모델로 정의하고, 자동 검증과 직렬화가 어떻게 동작하는지 학습합니다.

---

## 핵심 개념 (Core Concepts)

### 왜 Pydantic을 사용하는가?

REST API에서 클라이언트가 보내는 JSON 데이터는 문자열 형태입니다. 이를 Python 객체로 변환하고, 필수 필드 누락이나 잘못된 타입을 검증하는 작업이 필요합니다.

Pydantic은 이 과정을 자동화합니다:

```
클라이언트가 보낸 JSON 문자열
       │
       ▼
  Pydantic BaseModel
  ├── 1. JSON 파싱 (문자열 → Python dict)
  ├── 2. 타입 변환 (str → int, str → datetime 등)
  ├── 3. 필드 검증 (필수값, 범위, 패턴 등)
  └── 4. Python 객체 생성
       │
       ▼
  검증 통과 → 엔드포인트 함수에 전달
  검증 실패 → 422 에러 자동 응답
```

### Pydantic v2의 주요 특징

| 특징 | 설명 |
|------|------|
| Rust 기반 코어 | 검증 로직이 Rust로 구현되어 v1 대비 수 배 빠름 |
| `model_config` | 클래스 변수로 설정 (v1의 `class Config` 대체) |
| `model_dump()` | dict 변환 (v1의 `.dict()` 대체) |
| `model_validate()` | dict → 모델 변환 (v1의 `.parse_obj()` 대체) |

---

## 실습 코드 (Hands-on)

### Step 1: 기본 요청 모델 정의

**`schemas.py`** 파일을 생성합니다:

```python
# schemas.py
from pydantic import BaseModel, Field
from datetime import datetime


class ItemCreate(BaseModel):
    """아이템 생성 요청 스키마"""

    name: str = Field(
        ...,                          # 필수 필드
        min_length=1,
        max_length=100,
        description="아이템 이름",
        examples=["무선 키보드"],
    )
    price: float = Field(
        ...,
        gt=0,                         # 0 초과 (greater than)
        description="가격 (원)",
        examples=[89000],
    )
    description: str | None = Field(
        None,                         # 선택적 필드 (기본값 None)
        max_length=500,
        description="아이템 설명",
    )
    tags: list[str] = Field(
        default_factory=list,         # 기본값: 빈 리스트
        description="태그 목록",
        examples=[["전자", "무선"]],
    )
```

**`main.py`** 에서 사용합니다:

```python
# main.py
from fastapi import FastAPI
from schemas import ItemCreate

app = FastAPI()

items_db: list[dict] = []


@app.post("/items", status_code=201)
def create_item(item: ItemCreate):
    """
    요청 본문의 JSON이 ItemCreate 모델로 자동 파싱/검증됩니다.
    
    요청 예시:
    POST /items
    Content-Type: application/json
    {
        "name": "무선 키보드",
        "price": 89000,
        "tags": ["전자", "무선"]
    }
    """
    # item은 이미 검증된 ItemCreate 인스턴스
    item_dict = item.model_dump()   # Pydantic 모델 → dict 변환
    item_dict["id"] = len(items_db) + 1
    items_db.append(item_dict)
    return item_dict
```

### Step 2: 중첩 모델 (Nested Models)

복잡한 데이터 구조는 모델을 중첩하여 정의합니다:

```python
# schemas.py (이어서 추가)

class Address(BaseModel):
    """주소 스키마"""
    city: str
    street: str
    zip_code: str = Field(..., pattern=r"^\d{5}$")  # 5자리 숫자


class UserCreate(BaseModel):
    """사용자 생성 스키마 — Address 모델을 중첩"""
    username: str = Field(..., min_length=3, max_length=30)
    email: str
    address: Address                  # 중첩 모델
    phone_numbers: list[str] = Field(default_factory=list)
```

요청 예시:

```json
{
    "username": "hong",
    "email": "hong@example.com",
    "address": {
        "city": "서울",
        "street": "강남대로 123",
        "zip_code": "06000"
    },
    "phone_numbers": ["010-1234-5678"]
}
```

### Step 3: 검증 규칙 커스터마이징

Pydantic의 `field_validator`를 사용하여 커스텀 검증 로직을 추가합니다:

```python
# schemas.py (이어서 추가)
from pydantic import field_validator, model_validator


class OrderCreate(BaseModel):
    """주문 생성 스키마 — 커스텀 검증 포함"""
    product_name: str
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., gt=0)
    discount_rate: float = Field(0.0, ge=0, le=1)  # 0 ~ 1 사이 (0% ~ 100%)

    # 필드 단위 검증
    @field_validator("product_name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("product_name은 공백만으로 이루어질 수 없습니다")
        return v.strip()

    # 모델 전체 검증 (여러 필드의 관계 검증)
    @model_validator(mode="after")
    def check_discount_limit(self):
        """할인율이 50% 이상이면 수량 제한"""
        if self.discount_rate >= 0.5 and self.quantity > 10:
            raise ValueError("50% 이상 할인 시 수량은 10개 이하만 가능합니다")
        return self
```

### Step 4: 여러 Body 파라미터 조합

하나의 엔드포인트에서 여러 모델이나 추가 값을 받을 수 있습니다:

```python
# main.py (이어서 추가)
from fastapi import Body
from schemas import ItemCreate, UserCreate


@app.post("/orders")
def create_order(
    item: ItemCreate,                              # JSON 키: "item"
    buyer: UserCreate,                             # JSON 키: "buyer"
    note: str = Body(None, description="주문 비고"),# JSON 키: "note"
    urgent: bool = Body(False),                    # JSON 키: "urgent"
):
    """
    여러 Body 파라미터를 사용하면 JSON 구조가 자동으로 결정됩니다.
    
    요청 예시:
    {
        "item": {"name": "키보드", "price": 89000},
        "buyer": {"username": "hong", "email": "...", "address": {...}},
        "note": "빠른 배송 부탁드립니다",
        "urgent": true
    }
    """
    return {"item": item.model_dump(), "buyer": buyer.model_dump(), "note": note}
```

### Step 5: model_dump() 활용

Pydantic 모델을 Python dict로 변환할 때 유용한 옵션들:

```python
item = ItemCreate(name="노트북", price=1200000, description=None, tags=[])

# 기본 변환
item.model_dump()
# {"name": "노트북", "price": 1200000, "description": None, "tags": []}

# None 값 제외
item.model_dump(exclude_none=True)
# {"name": "노트북", "price": 1200000, "tags": []}

# 특정 필드만 포함
item.model_dump(include={"name", "price"})
# {"name": "노트북", "price": 1200000}

# 특정 필드 제외
item.model_dump(exclude={"tags"})
# {"name": "노트북", "price": 1200000, "description": None}

# JSON 문자열로 변환
item.model_dump_json()
# '{"name":"노트북","price":1200000,"description":null,"tags":[]}'
```

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- Pydantic `BaseModel`로 요청 본문 스키마 정의
- `Field`를 사용한 필드별 검증 규칙 설정
- 중첩 모델(Nested Models)로 복잡한 데이터 구조 표현
- `field_validator`, `model_validator`를 사용한 커스텀 검증
- 여러 Body 파라미터를 조합하는 방법
- `model_dump()` 옵션 활용

**다음 단계**: [04 — 응답 모델과 상태 코드](04-response-model-and-status.md)에서 API 응답을 체계적으로 관리하는 방법을 학습합니다.
