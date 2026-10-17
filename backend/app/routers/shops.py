from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import auth
from ..db import get_db
from ..errors import AppError, NotFoundError, ok

router = APIRouter(prefix="/api/shops", tags=["shops"], dependencies=[Depends(auth.require_auth)])


class ShopPayload(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    short_name: str = Field(default="", max_length=20)
    sort_order: int = 0


class ShopPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    short_name: str | None = Field(default=None, max_length=20)
    sort_order: int | None = None
    active: int | None = None


@router.get("")
def list_shops(include_inactive: bool = False):
    sql = "SELECT * FROM shops"
    if not include_inactive:
        sql += " WHERE active = 1"
    sql += " ORDER BY sort_order, id"
    with get_db() as db:
        rows = [dict(r) for r in db.execute(sql).fetchall()]
    return ok(rows)


@router.post("")
def create_shop(payload: ShopPayload):
    name = payload.name.strip()
    with get_db() as db:
        dup = db.execute("SELECT id FROM shops WHERE name = ?", (name,)).fetchone()
        if dup:
            raise AppError("店铺名已存在", 409, "duplicate_name")
        cur = db.execute(
            "INSERT INTO shops (name, short_name, sort_order, active) VALUES (?, ?, ?, 1)",
            (name, payload.short_name.strip(), payload.sort_order),
        )
        row = db.execute("SELECT * FROM shops WHERE id = ?", (cur.lastrowid,)).fetchone()
    return ok(dict(row))


@router.patch("/{shop_id}")
def update_shop(shop_id: int, payload: ShopPatch):
    with get_db() as db:
        current = db.execute("SELECT id FROM shops WHERE id = ?", (shop_id,)).fetchone()
        if not current:
            raise NotFoundError("店铺不存在")

        fields: list[str] = []
        values: list = []

        if payload.name is not None:
            name = payload.name.strip()
            dup = db.execute(
                "SELECT id FROM shops WHERE name = ? AND id <> ?", (name, shop_id)
            ).fetchone()
            if dup:
                raise AppError("店铺名已存在", 409, "duplicate_name")
            fields.append("name = ?")
            values.append(name)

        if payload.short_name is not None:
            fields.append("short_name = ?")
            values.append(payload.short_name.strip())

        if payload.sort_order is not None:
            fields.append("sort_order = ?")
            values.append(payload.sort_order)

        if payload.active is not None:
            fields.append("active = ?")
            values.append(payload.active)

        if not fields:
            raise AppError("没有需要更新的字段", 400, "empty_payload")

        values.append(shop_id)
        db.execute(f"UPDATE shops SET {', '.join(fields)} WHERE id = ?", values)
        row = db.execute("SELECT * FROM shops WHERE id = ?", (shop_id,)).fetchone()

    return ok(dict(row))
