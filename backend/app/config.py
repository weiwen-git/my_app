"""集中配置：全部来自环境变量，启动时集中校验，缺关键项直接失败。"""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
BACKUPS_DIR = PROJECT_DIR / "backups"


def _load_dotenv(path: Path) -> None:
    """极简 .env 解析，避免为了读一个文件引入额外依赖。不覆盖已存在的环境变量。"""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BACKEND_DIR / ".env")

USERNAME: str = os.environ.get("WB_USERNAME", "weiwen").strip()
PASSWORD_HASH: str = os.environ.get("WB_PASSWORD_HASH", "").strip()
PASSWORD_PLAIN: str = os.environ.get("WB_PASSWORD", "").strip()

_db_override = os.environ.get("WB_DB_PATH", "").strip()
DB_PATH: Path = Path(_db_override) if _db_override else (DATA_DIR / "workbench.db")

TIMEZONE: str = os.environ.get("TZ", "Asia/Shanghai").strip() or "Asia/Shanghai"

# 登录失败策略
MAX_LOGIN_FAILURES = 5
LOCK_SECONDS = 10 * 60

# 顺延上限
MAX_CARRY_DAYS = 7


def validate() -> None:
    """启动时校验，避免带着坏配置跑起来。"""
    if not USERNAME:
        raise RuntimeError("WB_USERNAME 未配置")

    if not PASSWORD_HASH and not PASSWORD_PLAIN:
        raise RuntimeError(
            "必须配置 WB_PASSWORD_HASH（生产）或 WB_PASSWORD（开发）。\n"
            "生成哈希：python backend/scripts/make-password.py"
        )

    if PASSWORD_PLAIN and not PASSWORD_HASH:
        print(
            "[warn] 正在使用明文密码 WB_PASSWORD，仅适合本地开发。"
            "上线前请改用 WB_PASSWORD_HASH。"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
