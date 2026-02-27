# 📁 05 — 폼 데이터와 파일 업로드

## 학습 목표 (Goal)

HTML 폼에서 전송되는 데이터(`application/x-www-form-urlencoded`)와 파일 업로드(`multipart/form-data`)를 FastAPI에서 처리하는 방법을 학습합니다.

---

## 핵심 개념 (Core Concepts)

### 콘텐츠 타입(Content-Type)에 따른 데이터 처리

클라이언트가 서버로 데이터를 보내는 방식은 `Content-Type` 헤더에 따라 달라집니다:

| Content-Type | 전송 형태 | FastAPI 처리 |
|-------------|-----------|-------------|
| `application/json` | JSON 본문 | Pydantic `BaseModel` |
| `application/x-www-form-urlencoded` | key=value 쌍 | `Form()` |
| `multipart/form-data` | 폼 필드 + 바이너리 파일 | `Form()` + `File()` / `UploadFile` |

> **참고**: 폼 데이터와 파일 업로드를 사용하려면 `python-multipart` 패키지가 필요합니다. 이미 `pyproject.toml`에 포함되어 있습니다.

### File vs UploadFile

| 항목 | `File(...)` | `UploadFile` |
|------|-------------|-------------|
| 타입 | `bytes` | `UploadFile` 객체 |
| 메모리 | 파일 전체를 메모리에 로드 | 일정 크기 이상은 디스크에 임시 저장 |
| 용도 | 작은 파일 (수 KB) | 대용량 파일 (이미지, 동영상 등) |
| 메타데이터 | 없음 | `filename`, `content_type`, `size` 제공 |

---

## 실습 코드 (Hands-on)

### Step 1: 폼 데이터 처리

```python
# main.py
from fastapi import FastAPI, Form

app = FastAPI()


@app.post("/login")
def login(
    username: str = Form(..., description="사용자 이름"),
    password: str = Form(..., description="비밀번호"),
):
    """
    HTML <form> 태그에서 전송되는 데이터를 처리합니다.
    
    Content-Type: application/x-www-form-urlencoded
    Body: username=hong&password=secret123
    """
    # 실제로는 DB에서 사용자 검증
    return {"username": username, "message": "로그인 성공"}


# 여러 폼 필드
@app.post("/feedback")
def submit_feedback(
    name: str = Form(...),
    email: str = Form(...),
    rating: int = Form(..., ge=1, le=5),    # 1~5 범위 검증
    message: str = Form("", max_length=1000),
):
    return {
        "name": name,
        "email": email,
        "rating": rating,
        "message": message,
    }
```

### Step 2: 단일 파일 업로드

```python
# main.py (이어서 추가)
from fastapi import File, UploadFile
import os


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File(..., description="업로드할 파일")):
    """
    파일 업로드 처리.
    UploadFile은 비동기 메서드를 제공하므로 async def를 사용합니다.
    
    UploadFile 주요 속성/메서드:
    - file.filename      → 원본 파일명
    - file.content_type   → MIME 타입 (예: image/png)
    - file.size           → 파일 크기 (bytes)
    - await file.read()   → 전체 내용 읽기
    - await file.seek(0)  → 읽기 위치 초기화
    """
    # 파일 크기 제한 (5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=413, detail="파일 크기는 5MB 이하만 허용됩니다")

    # 파일 저장
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "saved_to": file_path,
    }
```

### Step 3: 다중 파일 업로드

```python
# main.py (이어서 추가)

@app.post("/uploads")
async def upload_multiple_files(
    files: list[UploadFile] = File(..., description="여러 파일 업로드"),
):
    """다중 파일 업로드"""
    results = []
    for file in files:
        contents = await file.read()
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        results.append({
            "filename": file.filename,
            "size": len(contents),
        })
    return {"uploaded": len(results), "files": results}
```

### Step 4: 폼 데이터 + 파일 동시 처리

```python
# main.py (이어서 추가)

@app.post("/profile")
async def update_profile(
    username: str = Form(...),
    bio: str = Form(""),
    avatar: UploadFile = File(None),      # 파일은 선택적
):
    """
    폼 필드와 파일을 동시에 수신합니다.
    Content-Type: multipart/form-data
    
    주의: JSON body와 Form/File은 동시에 사용할 수 없습니다.
    """
    result = {"username": username, "bio": bio}

    if avatar:
        contents = await avatar.read()
        file_path = os.path.join(UPLOAD_DIR, avatar.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        result["avatar"] = avatar.filename

    return result
```

### Step 5: 파일 타입 검증

실전에서는 업로드 가능한 파일 형식을 제한합니다:

```python
# main.py (이어서 추가)
from fastapi import HTTPException

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@app.post("/images")
async def upload_image(image: UploadFile = File(...)):
    """이미지 파일만 허용하는 업로드 엔드포인트"""

    # MIME 타입 검증
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    contents = await image.read()

    # 파일 크기 검증 (10MB)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="이미지 크기는 10MB 이하만 허용됩니다")

    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    return {"filename": image.filename, "content_type": image.content_type}
```

---

## 마무리 및 다음 단계

이 단계에서 완료한 작업:
- `Form()`을 사용한 폼 데이터 수신 및 검증
- `UploadFile`을 사용한 단일/다중 파일 업로드
- 폼 데이터와 파일을 동시에 처리하는 방법
- 파일 타입과 크기 검증 패턴

**다음 단계**: [06 — 의존성 주입](06-dependency-injection.md)에서 FastAPI의 핵심 아키텍처 패턴인 의존성 주입(Dependency Injection)을 학습합니다.
