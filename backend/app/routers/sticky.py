"""便签：短内容卡片墙。清空已存在的便签才删除，新建的空卡片保留。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import auth
from ..db import get_db, now_iso
from ..errors import AppError, NotFoundError, ok

router = APIRouter(prefix="/api/sticky", tags=["sticky"], dependencies=[Depends(auth.require_auth)])

COLORS = ("yellow", "blue", "green", "pink", "gray")


class StickyPayload(BaseModel):
    content: str = Field(default="", max_length=500)
    color: str = "yellow"


class StickyPatch(BaseModel):
    content: str | None = Field(default=None, max_length=500)
    color: str | None = None
    pinned: int | None = None


def _check_color(value: str) -> str:
    if value not in COLORS:
        raise AppError("颜色不合法", 400, "bad_color")
    return value


@router.get("")
def list_sticky():
    with get_db() as db:
        rows = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM sticky_notes ORDER BY pinned DESC, sort_order, id DESC"
            ).fetchall()
        ]
    return ok(rows)


@router.post("")
def create_sticky(payload: StickyPayload):
    color = _check_color(payload.color)
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO sticky_notes (content, color, pinned, sort_order, created_at, updated_at) "
            "VALUES (?, ?, 0, 0, ?, ?)",
            (payload.content, color, now_iso(), now_iso()),
        )
        row = db.execute("SELECT * FROM sticky_notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return ok(dict(row))


@router.patch("/{sticky_id}")
def update_sticky(sticky_id: int, payload: StickyPatch):
    with get_db() as db:
        current = db.execute("SELECT * FROM sticky_notes WHERE id = ?", (sticky_id,)).fetchone()
        if not current:
            raise NotFoundError("便签不存在")

        # 原本有内容、被清空 → 删除（新建后从未输入的空卡片不受影响，因为它不会被 PATCH）
        if payload.content is not None and payload.content.strip() == "" and current["content"].strip():
            db.execute("DELETE FROM sticky_notes WHERE id = ?", (sticky_id,))
            return ok({"deleted": True, "id": sticky_id})

        fields: list[str] = []
        values: list = []
        if payload.content is not None:
            fields.append("content = ?")
            values.append(payload.content)
        if payload.color is not None:
            fields.append("color = ?")
            values.append(_check_color(payload.color))
        if payload.pinned is not None:
            fields.append("pinned = ?")
            values.append(1 if payload.pinned else 0)

        if not fields:
            raise AppError("没有需要更新的字段", 400, "empty_payload")

        fields.append("updated_at = ?")
        values.append(now_iso())
        values.append(sticky_id)
        db.execute(f"UPDATE sticky_notes SET {', '.join(fields)} WHERE id = ?", values)
        row = db.execute("SELECT * FROM sticky_notes WHERE id = ?", (sticky_id,)).fetchone()

    return ok({"deleted": False, "sticky": dict(row)})


@router.delete("/{sticky_id}")
def delete_sticky(sticky_id: int):
    with get_db() as db:
        cur = db.execute("DELETE FROM sticky_notes WHERE id = ?", (sticky_id,))
        if cur.rowcount == 0:
            raise NotFoundError("便签不存在")
    return ok(True)
