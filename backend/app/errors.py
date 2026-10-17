"""统一响应结构与类型化错误。客户端永远只看到 {ok, data, error}，看不到堆栈。"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """业务错误。status_code 决定 HTTP 状态，code 供前端做分支判断。"""

    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, status_code=404, code="not_found")


class AuthError(AppError):
    def __init__(self, message: str = "未登录或登录已失效", code: str = "unauthorized"):
        super().__init__(message, status_code=401, code=code)


def ok(data: Any = None) -> dict[str, Any]:
    return {"ok": True, "data": data, "error": None}


def _fail(message: str, code: str, status_code: int, details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "data": None,
            "error": {"code": code, "message": message, "details": details},
        },
    )


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _fail(exc.message, exc.code, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "请求参数"
        return _fail(
            f"{field} 不合法：{first.get('msg', '格式错误')}",
            "validation_error",
            422,
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        # 只写日志，不把细节返回给客户端
        print(f"[error] unhandled: {type(exc).__name__}: {exc}")
        return _fail("服务器内部错误", "internal_error", 500)
