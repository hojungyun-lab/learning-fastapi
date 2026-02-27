# app/exceptions.py — 커스텀 예외 클래스
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """앱 예외의 기본 클래스"""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code


class DuplicateError(AppException):
    def __init__(self, field: str, value: str):
        super().__init__(
            message=f"이미 등록된 {field}입니다: {value}",
            code="DUPLICATE",
            status_code=409,
        )


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            message=f"{resource}(ID: {resource_id})을 찾을 수 없습니다",
            code="NOT_FOUND",
            status_code=404,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "접근 권한이 없습니다"):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """AppException 커스텀 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
