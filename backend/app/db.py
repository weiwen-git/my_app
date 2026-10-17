"""SQLite 访问层：建表、连接管理、时间工具。

时区一律按 Asia/Shanghai，避免容器 UTC 导致的"今天"错位。
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config

try:
    TZ = ZoneInfo(config.TIMEZONE)
except Exception:  # 环境缺 tzdata 时的兜底：固定 UTC+8
    from datetime import timezone as _timezone

    TZ = _timezone(timedelta(hours=8), name=config.TIMEZONE)

SCHEMA = """
CREATE TABLE IF NOT EXISTS shops (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT    NOT NULL,
  short_name  TEXT    DEFAULT '',
  sort_order  INTEGER DEFAULT 0,
  active      INTEGER DEFAULT 1,
  created_at  TEXT    DEFAULT (datetime('now','+8 hours'))
);

CREATE TABLE IF NOT EXISTS task_templates (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  shop_id     INTEGER NOT NULL,
  title       TEXT    NOT NULL,
  repeat_rule TEXT    NOT NULL,
  sort_order  INTEGER DEFAULT 0,
  active      INTEGER DEFAULT 1,
  created_at  TEXT    DEFAULT (datetime('now','+8 hours'))
);

CREATE TABLE IF NOT EXISTS task_instances (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  template_id INTEGER,
  shop_id     INTEGER NOT NULL,
  title       TEXT    NOT NULL,
  period_type TEXT    NOT NULL,
  task_date   TEXT    NOT NULL,
  origin_date TEXT    NOT NULL,
  status      TEXT    DEFAULT 'todo',
  carried     INTEGER DEFAULT 0,
  note        TEXT    DEFAULT '',
  done_at     TEXT,
  created_at  TEXT    DEFAULT (datetime('now','+8 hours'))
);

CREATE TABLE IF NOT EXISTS todos (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT    NOT NULL,
  note        TEXT    DEFAULT '',
  priority    TEXT    DEFAULT 'normal',
  due_date    TEXT,
  status      TEXT    DEFAULT 'todo',
  done_at     TEXT,
  created_at  TEXT    DEFAULT (datetime('now','+8 hours'))
);

CREATE TABLE IF NOT EXISTS sticky_notes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  content     TEXT    NOT NULL,
  color       TEXT    DEFAULT 'yellow',
  pinned      INTEGER DEFAULT 0,
  sort_order  INTEGER DEFAULT 0,
  created_at  TEXT    DEFAULT (datetime('now','+8 hours')),
  updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS notes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT    NOT NULL,
  content     TEXT    DEFAULT '',
  created_at  TEXT    DEFAULT (datetime('now','+8 hours')),
  updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS data_sheets (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT    NOT NULL,
  sort_order  INTEGER DEFAULT 0,
  active      INTEGER DEFAULT 1,
  created_at  TEXT    DEFAULT (datetime('now','+8 hours'))
);

CREATE TABLE IF NOT EXISTS data_columns (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  sheet_id    INTEGER NOT NULL,
  name        TEXT    NOT NULL,
  type        TEXT    DEFAULT 'number',
  agg         TEXT    DEFAULT 'sum',
  sort_order  INTEGER DEFAULT 0,
  FOREIGN KEY (sheet_id) REFERENCES data_sheets(id)
);

CREATE TABLE IF NOT EXISTS data_rows (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  sheet_id    INTEGER NOT NULL,
  values_json TEXT    NOT NULL DEFAULT '{}',
  sort_order  INTEGER DEFAULT 0,
  created_at  TEXT    DEFAULT (datetime('now','+8 hours')),
  FOREIGN KEY (sheet_id) REFERENCES data_sheets(id)
);

CREATE INDEX IF NOT EXISTS idx_task_date     ON task_instances(task_date);
CREATE INDEX IF NOT EXISTS idx_task_shop     ON task_instances(shop_id, task_date);
CREATE INDEX IF NOT EXISTS idx_template_shop ON task_templates(shop_id, active);
CREATE INDEX IF NOT EXISTS idx_col_sheet     ON data_columns(sheet_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_row_sheet     ON data_rows(sheet_id);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """一次请求一个连接，自动提交/回滚/关闭。"""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as db:
        db.executescript(SCHEMA)


# ---------- 时间工具 ----------

def today() -> date:
    return datetime.now(TZ).date()


def now_iso() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")


def d(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def last_day_of_month(day: date) -> int:
    """当月最后一天是几号。用于「每月 31 号」在 2 月的兜底。"""
    nxt = date(day.year + (1 if day.month == 12 else 0), 1 if day.month == 12 else day.month + 1, 1)
    return (nxt - timedelta(days=1)).day
