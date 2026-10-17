from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Request, Response
from pydantic import BaseModel, Field

from .. import auth
from ..errors import AppError, AuthError, ok

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "wb_session"


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login")
def do_login(payload: LoginPayload, request: Request, response: Response):
    ip = _client_ip(request)

    remain = auth.locked_seconds(ip)
    if remain > 0:
        raise AppError(f"尝试次数过多，请 {remain // 60 + 1} 分钟后再试", 429, "locked")

    try:
        token = auth.login(payload.username.strip(), payload.password)
    except AuthError:
        auth.register_failure(ip)
        raise

    auth.clear_failures(ip)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # 生产走 HTTPS 时应设为 True（由 Nginx 终止 TLS）
        max_age=auth.SESSION_TTL,
        path="/",
    )
    return ok({"username": payload.username.strip()})


@router.post("/logout")
def do_logout(response: Response, wb_session: str | None = Cookie(default=None)):
    auth.logout(wb_session)
    response.delete_cookie(COOKIE_NAME, path="/")
    return ok(True)


@router.get("/me")
def me(_: str = Depends(auth.require_auth)):
    from .. import config

    return ok({"username": config.USERNAME})
