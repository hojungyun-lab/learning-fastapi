# main.py — FastAPI 기초 단계 통합 데모
#
# docs 00~06의 내용을 통합한 in-memory CRUD API입니다.
# 실행: poetry run uvicorn main:app --reload
# 문서: http://127.0.0.1:8000/docs

from fastapi import FastAPI, HTTPException, Query, Path, status
from schemas import ItemCreate, ItemUpdate, ItemResponse
from enum import Enum

app = FastAPI(
    title="Basic Items API",
    description="FastAPI 기초 학습 데모 — in-memory CRUD API",
    version="0.1.0",
)


# ──────────────────────────────────────────────
# 데이터 저장소 (in-memory)
# ──────────────────────────────────────────────
items_db: dict[int, dict] = {
    1: {"id": 1, "name": "노트북", "price": 1200000, "description": "15인치 노트북", "tags": ["전자", "컴퓨터"]},
    2: {"id": 2, "name": "마우스", "price": 35000, "description": "무선 마우스", "tags": ["전자", "주변기기"]},
    3: {"id": 3, "name": "키보드", "price": 89000, "description": None, "tags": ["전자"]},
}
_next_id = 4


class SortField(str, Enum):
    """정렬 가능 필드"""
    name = "name"
    price = "price"


# ──────────────────────────────────────────────
# GET — 목록 조회 (쿼리 파라미터, 페이지네이션, 검색)
# ──────────────────────────────────────────────
@app.get("/items", response_model=list[ItemResponse])
def list_items(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=1, le=100, description="조회할 최대 항목 수"),
    search: str | None = Query(None, min_length=1, description="이름 검색어"),
    min_price: float | None = Query(None, ge=0, description="최소 가격"),
    max_price: float | None = Query(None, ge=0, description="최대 가격"),
    sort_by: SortField | None = Query(None, description="정렬 기준"),
):
    """아이템 목록 조회 — 필터, 검색, 정렬, 페이지네이션 지원"""
    results = list(items_db.values())

    # 검색 필터
    if search:
        results = [i for i in results if search.lower() in i["name"].lower()]
    if min_price is not None:
        results = [i for i in results if i["price"] >= min_price]
    if max_price is not None:
        results = [i for i in results if i["price"] <= max_price]

    # 정렬
    if sort_by:
        results.sort(key=lambda x: x[sort_by.value])

    # 페이지네이션
    return results[skip : skip + limit]


# ──────────────────────────────────────────────
# GET — 단건 조회 (경로 파라미터)
# ──────────────────────────────────────────────
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int = Path(..., ge=1, description="아이템 ID"),
):
    """아이템 단건 조회"""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아이템(ID: {item_id})을 찾을 수 없습니다",
        )
    return items_db[item_id]


# ──────────────────────────────────────────────
# POST — 생성 (Pydantic 요청 모델)
# ──────────────────────────────────────────────
@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
    """새 아이템 생성"""
    global _next_id
    item_data = {"id": _next_id, **item.model_dump()}
    items_db[_next_id] = item_data
    _next_id += 1
    return item_data


# ──────────────────────────────────────────────
# PATCH — 부분 수정 (exclude_unset)
# ──────────────────────────────────────────────
@app.patch("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int = Path(..., ge=1),
    item: ItemUpdate = ...,
):
    """아이템 부분 수정 — 전달된 필드만 업데이트"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    stored = items_db[item_id]
    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        stored[field] = value

    return stored


# ──────────────────────────────────────────────
# DELETE — 삭제
# ──────────────────────────────────────────────
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int = Path(..., ge=1)):
    """아이템 삭제"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
    del items_db[item_id]
