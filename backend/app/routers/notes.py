"""笔记：标题 + 纯文本正文。不做富文本。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from .. import auth
from ..db import get_db, now_iso
from ..errors import AppError, NotFoundError, ok

router = APIRouter(prefix="/api/notes", tags=["notes"], dependencies=[Depends(auth.require_auth)])


class NotePayload(BaseModel):
    title: str = Field(default="未命名", max_length=80)
    content: str = Field(default="", max_length=50000)


class NotePatch(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    content: str | None = Field(default=None, max_length=50000)


@router.get("")
def list_notes(q: str = Query(default="")):
    sql = "SELECT id, title, substr(content, 1, 60) AS excerpt, updated_at, created_at FROM notes"
    params: list = []
    if q.strip():
        sql += " WHERE title LIKE ?"
        params.append(f"%{q.strip()}%")
    sql += " ORDER BY updated_at DESC, id DESC"
    with get_db() as db:
        rows = [dict(r) for r in db.execute(sql, params).fetchall()]
    return ok(rows)


@router.get("/{note_id}")
def get_note(note_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        raise NotFoundError("笔记不存在")
    return ok(dict(row))


@router.post("")
def create_note(payload: NotePayload):
    title = payload.title.strip() or "未命名"
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, payload.content, now_iso(), now_iso()),
        )
        row = db.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return ok(dict(row))


@router.patch("/{note_id}")
def update_note(note_id: int, payload: NotePatch):
    fields: list[str] = []
    values: list = []
    if payload.title is not None:
        fields.append("title = ?")
        values.append(payload.title.strip() or "未命名")
    if payload.content is not None:
        fields.append("content = ?")
        values.append(payload.content)

    if not fields:
        raise AppError("没有需要更新的字段", 400, "empty_payload")

    fields.append("updated_at = ?")
    values.append(now_iso())
    values.append(note_id)

    with get_db() as db:
        cur = db.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id = ?", values)
        if cur.rowcount == 0:
            raise NotFoundError("笔记不存在")
        row = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return ok(dict(row))


@router.delete("/{note_id}")
def delete_note(note_id: int):
    with get_db() as db:
        cur = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        if cur.rowcount == 0:
            raise NotFoundError("笔记不存在")
    return ok(True)
