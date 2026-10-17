"""待办：临时接到的、不属于任何店铺的事。无店铺、无周期。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import auth
from ..db import get_db, now_iso
from ..errors import AppError, NotFoundError, ok

router = APIRouter(prefix="/api/todos", tags=["todos"], dependencies=[Depends(auth.require_auth)])

PRIORITIES = ("low", "normal", "high")


class TodoPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    note: str = Field(default="", max_length=2000)
    priority: str = "normal"
    due_date: str | None = None


class TodoPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    note: str | None = Field(default=None, max_length=2000)
    priority: str | None = None
    due_date: str | None = None
    status: str | None = None


def _check_priority(value: str) -> str:
    if value not in PRIORITIES:
        raise AppError("优先级只能是 low / normal / high", 400, "bad_priority")
    return value


def _row(row) -> dict:
    return dict(row)


@router.get("")
def list_todos():
    with get_db() as db:
        todo = [
            _row(r)
            for r in db.execute(
                "SELECT * FROM todos WHERE status = 'todo' "
                "ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, "
                "CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date, id DESC"
            ).fetchall()
        ]
        done = [
            _row(r)
            for r in db.execute(
                "SELECT * FROM todos WHERE status = 'done' ORDER BY done_at DESC LIMIT 200"
            ).fetchall()
        ]
    return ok({"todo": todo, "done": done})


@router.post("")
def create_todo(payload: TodoPayload):
    priority = _check_priority(payload.priority)
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO todos (title, note, priority, due_date, status, created_at) "
            "VALUES (?, ?, ?, ?, 'todo', ?)",
            (payload.title.strip(), payload.note.strip(), priority, payload.due_date or None, now_iso()),
        )
        row = db.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return ok(dict(row))


@router.patch("/{todo_id}")
def update_todo(todo_id: int, payload: TodoPatch):
    fields: list[str] = []
    values: list = []

    if payload.title is not None:
        fields.append("title = ?")
        values.append(payload.title.strip())
    if payload.note is not None:
        fields.append("note = ?")
        values.append(payload.note.strip())
    if payload.priority is not None:
        fields.append("priority = ?")
        values.append(_check_priority(payload.priority))
    if payload.due_date is not None:
        fields.append("due_date = ?")
        values.append(payload.due_date or None)
    if payload.status is not None:
        if payload.status not in ("todo", "done"):
            raise AppError("状态只能是 todo / done", 400, "bad_status")
        fields.append("status = ?")
        values.append(payload.status)
        fields.append("done_at = ?")
        values.append(now_iso() if payload.status == "done" else None)

    if not fields:
        raise AppError("没有需要更新的字段", 400, "empty_payload")

    values.append(todo_id)
    with get_db() as db:
        cur = db.execute(f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", values)
        if cur.rowcount == 0:
            raise NotFoundError("待办不存在")
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return ok(dict(row))


@router.delete("/{todo_id}")
def delete_todo(todo_id: int):
    with get_db() as db:
        cur = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cur.rowcount == 0:
            raise NotFoundError("待办不存在")
    return ok(True)
