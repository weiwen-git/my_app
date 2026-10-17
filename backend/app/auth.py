"""单用户鉴权：用户名 + 密码，Session 存服务端内存。

单用户不等于不要登录 —— 公网暴露后端口扫描是常态，所以所有 /api 必须过 require_auth。
"""

from __future__ import annotations

import secrets
import time
from typing import Annotated

import bcrypt
from fastapi import Cookie, Depends

from . import config
from .errors import AuthError

# token -> 创建时间戳
_sessions: dict[str, float] = {}
# ip -> {"fails": int, "until": float}
_failures: dict[str, dict] = {}

SESSION_TTL = 7 * 24 * 3600  # 7 天；进程重启即全部失效，单用户可接受


def _verify_password(password: str) -> bool:
    if config.PASSWORD_HASH:
        try:
            return bcrypt.checkpw(password.encode(), config.PASSWORD_HASH.encode())
        except ValueError:
            return False
    if config.PASSWORD_PLAIN:
        return secrets.compare_digest(password, config.PASSWORD_PLAIN)
    return False


def locked_seconds(ip: str) -> int:
    rec = _failures.get(ip)
    if not rec:
        return 0
    remain = int(rec.get("until", 0) - time.time())
    if remain <= 0:
        _failures.pop(ip, None)
        return 0
    return remain


def register_failure(ip: str) -> None:
    rec = _failures.setdefault(ip, {"fails": 0, "until": 0})
    rec["fails"] += 1
    if rec["fails"] >= config.MAX_LOGIN_FAILURES:
        rec["until"] = time.time() + config.LOCK_SECONDS
        rec["fails"] = 0


def clear_failures(ip: str) -> None:
    _failures.pop(ip, None)


def login(username: str, password: str) -> str:
    if not (secrets.compare_digest(username, config.USERNAME) and _verify_password(password)):
        raise AuthError("用户名或密码错误", code="bad_credentials")
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.time()
    return token


def logout(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


def _valid(token: str | None) -> bool:
    if not token:
        return False
    created = _sessions.get(token)
    if created is None:
        return False
    if time.time() - created > SESSION_TTL:
        _sessions.pop(token, None)
        return False
    return True


def require_auth(session: Annotated[str | None, Cookie(alias="wb_session")] = None) -> str:
    """所有业务路由的依赖。未登录统一 401，前端据此跳登录页。"""
    if not _valid(session):
        raise AuthError()
    return session  # type: ignore[return-value]


AuthDep = Annotated[str, Depends(require_auth)]
