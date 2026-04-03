# app/routers/todos.py — Todo CRUD 라우터
from fastapi import APIRouter, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.dependencies import DbSession, CurrentUser, Pagination
from app.exceptions import NotFoundError, ForbiddenError
from app.models import Todo
from app.schemas import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse

router = APIRouter(prefix="/todos", tags=["Todos"])


def _get_user_todo(db: Session, todo_id: int, user_id: int) -> Todo:
    """사용자 소유의 Todo를 조회하고, 없거나 권한이 없으면 예외 발생"""
    todo = db.scalar(select(Todo).where(Todo.id == todo_id))
    if not todo:
        raise NotFoundError("Todo", todo_id)
    if todo.owner_id != user_id:
        raise ForbiddenError("이 Todo에 대한 접근 권한이 없습니다")
    return todo


@router.get("", response_model=TodoListResponse)
def list_todos(
    db: DbSession,
    user: CurrentUser,
    pagination: Pagination,
    completed: bool | None = Query(None, description="완료 여부 필터"),
    search: str | None = Query(None, min_length=1, description="제목 검색"),
    priority: int | None = Query(None, ge=0, le=2, description="우선순위 필터"),
):
    """
    현재 사용자의 Todo 목록 조회.
    필터, 검색, 페이지네이션을 지원합니다.
    """
    stmt = select(Todo).where(Todo.owner_id == user.id)

    if completed is not None:
        stmt = stmt.where(Todo.completed == completed)
    if search:
        stmt = stmt.where(Todo.title.ilike(f"%{search}%"))
    if priority is not None:
        stmt = stmt.where(Todo.priority == priority)

    # 전체 개수 조회
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    # 페이징된 결과 조회
    items_stmt = (
        stmt.order_by(Todo.priority.desc(), Todo.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = db.scalars(items_stmt).all()

    return TodoListResponse(total=total, items=list(items))


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, db: DbSession, user: CurrentUser):
    """새 Todo 생성"""
    db_todo = Todo(**todo.model_dump(), owner_id=user.id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: DbSession, user: CurrentUser):
    """Todo 단건 조회"""
    return _get_user_todo(db, todo_id, user.id)


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate, db: DbSession, user: CurrentUser):
    """Todo 부분 수정"""
    db_todo = _get_user_todo(db, todo_id, user.id)

    update_data = todo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)

    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: DbSession, user: CurrentUser):
    """Todo 삭제"""
    db_todo = _get_user_todo(db, todo_id, user.id)
    db.delete(db_todo)
    db.commit()
