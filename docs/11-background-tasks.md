# ⏳ 11 — 백그라운드 태스크

## 학습 목표 (Goal)

FastAPI의 `BackgroundTasks`를 사용하여 응답을 먼저 반환하고, 시간이 걸리는 작업을 별도로 실행하는 방법을 학습합니다.

---

## 핵심 개념 (Core Concepts)

### 왜 백그라운드 태스크가 필요한가?

API 엔드포인트에서 이메일 발송, 로그 기록, 데이터 집계 등 시간이 소요되는 작업을 직접 수행하면, 클라이언트는 해당 작업이 완료될 때까지 응답을 기다려야 합니다.

```
(백그라운드 태스크 미사용)
요청 → 주문 생성 → 이메일 발송(3초) → 응답 반환
                                        총 대기: ~3초

(백그라운드 태스크 사용)
요청 → 주문 생성 → 응답 반환 (즉시)
                     └→ 이메일 발송(3초, 백그라운드)
                        총 대기: ~0.1초
```

### BackgroundTasks vs 외부 태스크 큐

| 항목 | BackgroundTasks | Celery / ARQ |
|------|----------------|-------------|
| 실행 위치 | 같은 프로세스 내 | 별도 워커 프로세스 |
| 설정 복잡도 | 없음 (FastAPI 내장) | Redis/RabbitMQ 등 브로커 필요 |
| 신뢰성 | 서버 재시작 시 유실 | 태스크 큐에 보관, 재시도 가능 |
| 적합한 작업 | 로그 기록, 알림, 캐시 갱신 | 이미지 처리, 대규모 연산, 결제 |

> `BackgroundTasks`는 가벼운 비동기 작업에 적합합니다. 실패 시 재시도가 필요하거나 처리 시간이 긴 작업은 Celery 등 별도 태스크 큐를 권장합니다.

---

## 실습 코드 (Hands-on)

### Step 1: 기본 사용법

```python
# main.py
import time
import logging
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, EmailStr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


# --------------------------------------------------
# 백그라운드에서 실행될 함수들
# --------------------------------------------------
def send_email(to: str, subject: str, body: str):
    """
    이메일 발송 (시뮬레이션).
    실제로는 SMTP 라이브러리나 외부 API를 호출합니다.
    """
    logger.info(f"이메일 발송 시작: to={to}, subject={subject}")
    time.sleep(3)  # 발송에 3초 소요 (시뮬레이션)
    logger.info(f"이메일 발송 완료: to={to}")


def write_audit_log(user_id: int, action: str, detail: str):
    """감사 로그 기록"""
    logger.info(f"[AUDIT] user={user_id} action={action} detail={detail}")


# --------------------------------------------------
# 엔드포인트에서 BackgroundTasks 사용
# --------------------------------------------------
class OrderCreate(BaseModel):
    product_name: str
    quantity: int
    email: EmailStr


@app.post("/orders", status_code=201)
def create_order(order: OrderCreate, background_tasks: BackgroundTasks):
    """
    BackgroundTasks를 파라미터로 선언하면 FastAPI가 자동으로 주입합니다.
    
    add_task(함수, 인자1, 인자2, ...)로 백그라운드 작업을 등록합니다.
    응답은 즉시 반환되고, 등록된 작업들은 응답 반환 후 순차적으로 실행됩니다.
    """
    # 주문 생성 로직
    order_id = 1  # 실제로는 DB에 저장 후 ID 반환

    # 백그라운드 태스크 등록 (여러 개 가능)
    background_tasks.add_task(
        send_email,
        to=order.email,
        subject="주문 확인",
        body=f"주문 #{order_id} ({order.product_name} x {order.quantity})",
    )
    background_tasks.add_task(
        write_audit_log,
        user_id=1,
        action="CREATE_ORDER",
        detail=f"order_id={order_id}",
    )

    # 응답은 즉시 반환 (이메일 발송을 기다리지 않음)
    return {"order_id": order_id, "status": "created"}
```

### Step 2: 의존성에서 BackgroundTasks 사용

의존성 함수 내에서도 백그라운드 태스크를 등록할 수 있습니다:

```python
# dependencies.py
from fastapi import BackgroundTasks, Depends, Header, HTTPException
import logging

logger = logging.getLogger(__name__)


def log_api_usage(api_key: str, endpoint: str):
    """API 사용량 기록 (백그라운드)"""
    logger.info(f"[API USAGE] key={api_key} endpoint={endpoint}")


async def verify_api_key(
    x_api_key: str = Header(...),
    background_tasks: BackgroundTasks = None,
):
    """
    API 키 검증 의존성.
    검증 후 사용량을 백그라운드로 기록합니다.
    """
    valid_keys = {"key-001", "key-002", "key-003"}
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 의존성 내에서 백그라운드 태스크 등록
    if background_tasks:
        background_tasks.add_task(log_api_usage, x_api_key, "endpoint")

    return x_api_key
```

### Step 3: async 함수도 사용 가능

```python
# main.py (이어서 추가)
import asyncio


async def send_webhook(url: str, payload: dict):
    """
    비동기 백그라운드 태스크.
    async 함수를 사용하면 이벤트 루프에서 비동기로 실행됩니다.
    """
    logger.info(f"Webhook 전송 시작: {url}")
    await asyncio.sleep(2)  # 비동기 대기 (시뮬레이션)
    logger.info(f"Webhook 전송 완료: {url} payload={payload}")


@app.post("/events")
async def create_event(background_tasks: BackgroundTasks):
    """async 함수를 백그라운드 태스크로 사용하는 예시"""
    event = {"type": "user_signup", "user_id": 42}

    background_tasks.add_task(
        send_webhook,
        url="https://hooks.example.com/events",
        payload=event,
    )

    return {"event": event, "webhook": "scheduled"}
```

### Step 4: 실행 및 동작 확인

```bash
poetry run uvicorn main:app --reload
```

Swagger UI에서 `POST /orders`를 호출하면:

1. 응답이 즉시 반환됩니다 (이메일 발송 전)
2. 서버 콘솔에서 백그라운드 태스크 로그가 순차적으로 출력됩니다:
   ```
   INFO: 이메일 발송 시작: to=user@example.com, subject=주문 확인
   INFO: [AUDIT] user=1 action=CREATE_ORDER detail=order_id=1
   INFO: 이메일 발송 완료: to=user@example.com
   ```

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- `BackgroundTasks`를 사용한 응답 후 비동기 작업 실행
- 여러 백그라운드 태스크 등록 방법
- 의존성 내에서 백그라운드 태스크 사용
- 동기/비동기 태스크 함수 모두 지원 가능

**다음 단계**: [12 — 테스팅](12-testing.md)에서 FastAPI 앱을 체계적으로 테스트하는 방법을 학습합니다.
