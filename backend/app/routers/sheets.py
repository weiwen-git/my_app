"""数据表：自定义列 + JSON 存值。

设计取舍：行值统一存 values_json（{"<column_id>": value}），而不是每列建字段。
代价是聚合要解析 JSON，收益是「加列永不改表结构」——这是自定义列功能的成立前提。
"""

from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import auth
from ..db import get_db, now_iso
from ..errors import AppError, NotFoundError, ok

router = APIRouter(prefix="/api/sheets", tags=["sheets"], dependencies=[Depends(auth.require_auth)])

COL_TYPES = ("number", "text", "date")
AGG_TYPES = ("sum", "avg", "none")


# ---------------- 工具 ----------------

def _sheet_or_404(db, sheet_id: int):
    row = db.execute("SELECT * FROM data_sheets WHERE id = ? AND active = 1", (sheet_id,)).fetchone()
    if not row:
        raise NotFoundError("数据表不存在")
    return row


def _load_columns(db, sheet_id: int) -> list[dict]:
    return [
        dict(r)
        for r in db.execute(
            "SELECT * FROM data_columns WHERE sheet_id = ? ORDER BY sort_order, id", (sheet_id,)
        ).fetchall()
    ]


def _parse_values(raw: str) -> dict:
    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_value(col_type: str, value):
    """按列类型收敛值。数字列存数字，其他存字符串，空值统一 None。"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if col_type == "number":
        try:
            num = float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            raise AppError(f"「{value}」不是有效数字", 400, "bad_number")
        return int(num) if num.is_integer() else num
    return str(value).strip()


def _check_unique_name(columns: list[dict], name: str, exclude_id: int | None = None) -> None:
    for col in columns:
        if col["id"] == exclude_id:
            continue
        if col["name"].strip() == name.strip():
            raise AppError("同一张表内列名不能重复", 409, "duplicate_column")


def _check_type_change(db, sheet_id: int, col_id: int, new_type: str) -> None:
    """改成数字列前，确认已有值都能转数字，否则会把脏数据带进合计。"""
    if new_type != "number":
        return
    rows = db.execute("SELECT values_json FROM data_rows WHERE sheet_id = ?", (sheet_id,)).fetchall()
    key = str(col_id)
    for idx, row in enumerate(rows, start=1):
        value = _parse_values(row["values_json"]).get(key)
        if value in (None, ""):
            continue
        try:
            float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            raise AppError(
                f"第 {idx} 行的值「{value}」不是数字，无法把该列改为数字类型",
                400,
                "bad_type_change",
            )


# ---------------- 数据表 ----------------

class SheetPayload(BaseModel):
    name: str = Field(min_length=1, max_length=40)


@router.get("")
def list_sheets():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT s.id, s.name, s.sort_order,
                   (SELECT COUNT(*) FROM data_columns c WHERE c.sheet_id = s.id) AS column_count,
                   (SELECT COUNT(*) FROM data_rows r WHERE r.sheet_id = s.id) AS row_count,
                   (SELECT MAX(r.created_at) FROM data_rows r WHERE r.sheet_id = s.id) AS updated_at
            FROM data_sheets s
            WHERE s.active = 1
            ORDER BY s.sort_order, s.id
            """
        ).fetchall()
    return ok([dict(r) for r in rows])


@router.post("")
def create_sheet(payload: SheetPayload):
    name = payload.name.strip()
    with get_db() as db:
        dup = db.execute("SELECT id FROM data_sheets WHERE name = ? AND active = 1", (name,)).fetchone()
        if dup:
            raise AppError("数据表名已存在", 409, "duplicate_name")
        cur = db.execute(
            "INSERT INTO data_sheets (name, sort_order, active, created_at) VALUES (?, 0, 1, ?)",
            (name, now_iso()),
        )
        sheet_id = cur.lastrowid
        # 新建表默认给一列日期，避免进去是一片空白
        db.execute(
            "INSERT INTO data_columns (sheet_id, name, type, agg, sort_order) VALUES (?, '日期', 'date', 'none', 0)",
            (sheet_id,),
        )
        row = db.execute("SELECT * FROM data_sheets WHERE id = ?", (sheet_id,)).fetchone()
    return ok(dict(row))


@router.get("/{sheet_id}")
def get_sheet(sheet_id: int):
    with get_db() as db:
        sheet = _sheet_or_404(db, sheet_id)
        columns = _load_columns(db, sheet_id)
        rows = []
        for r in db.execute(
            "SELECT * FROM data_rows WHERE sheet_id = ? ORDER BY created_at DESC, id DESC", (sheet_id,)
        ).fetchall():
            rows.append(
                {
                    "id": r["id"],
                    "values": _parse_values(r["values_json"]),
                    "created_at": r["created_at"],
                }
            )
    return ok({"sheet": dict(sheet), "columns": columns, "rows": rows})


@router.patch("/{sheet_id}")
def rename_sheet(sheet_id: int, payload: SheetPayload):
    name = payload.name.strip()
    with get_db() as db:
        _sheet_or_404(db, sheet_id)
        dup = db.execute(
            "SELECT id FROM data_sheets WHERE name = ? AND active = 1 AND id <> ?", (name, sheet_id)
        ).fetchone()
        if dup:
            raise AppError("数据表名已存在", 409, "duplicate_name")
        db.execute("UPDATE data_sheets SET name = ? WHERE id = ?", (name, sheet_id))
        row = db.execute("SELECT * FROM data_sheets WHERE id = ?", (sheet_id,)).fetchone()
    return ok(dict(row))


@router.delete("/{sheet_id}")
def delete_sheet(sheet_id: int):
    with get_db() as db:
        cur = db.execute("UPDATE data_sheets SET active = 0 WHERE id = ?", (sheet_id,))
        if cur.rowcount == 0:
            raise NotFoundError("数据表不存在")
    return ok(True)


# ---------------- 列 ----------------

class ColumnPayload(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    type: str = "number"
    agg: str = "sum"


class ColumnPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)
    type: str | None = None
    agg: str | None = None
    sort_order: int | None = None


@router.post("/{sheet_id}/columns")
def create_column(sheet_id: int, payload: ColumnPayload):
    if payload.type not in COL_TYPES:
        raise AppError("列类型不合法", 400, "bad_type")
    if payload.agg not in AGG_TYPES:
        raise AppError("合计方式不合法", 400, "bad_agg")

    with get_db() as db:
        _sheet_or_404(db, sheet_id)
        columns = _load_columns(db, sheet_id)
        _check_unique_name(columns, payload.name)
        next_order = (max([c["sort_order"] for c in columns], default=-1)) + 1
        cur = db.execute(
            "INSERT INTO data_columns (sheet_id, name, type, agg, sort_order) VALUES (?, ?, ?, ?, ?)",
            (sheet_id, payload.name.strip(), payload.type, payload.agg if payload.type == "number" else "none", next_order),
        )
        row = db.execute("SELECT * FROM data_columns WHERE id = ?", (cur.lastrowid,)).fetchone()
    return ok(dict(row))


@router.patch("/{sheet_id}/columns/{column_id}")
def update_column(sheet_id: int, column_id: int, payload: ColumnPatch):
    with get_db() as db:
        _sheet_or_404(db, sheet_id)
        current = db.execute(
            "SELECT * FROM data_columns WHERE id = ? AND sheet_id = ?", (column_id, sheet_id)
        ).fetchone()
        if not current:
            raise NotFoundError("列不存在")

        columns = _load_columns(db, sheet_id)

        if payload.name is not None:
            _check_unique_name(columns, payload.name, exclude_id=column_id)

        if payload.type is not None:
            if payload.type not in COL_TYPES:
                raise AppError("列类型不合法", 400, "bad_type")
            _check_type_change(db, sheet_id, column_id, payload.type)

        if payload.agg is not None and payload.agg not in AGG_TYPES:
            raise AppError("合计方式不合法", 400, "bad_agg")

        fields: list[str] = []
        values: list = []
        if payload.name is not None:
            fields.append("name = ?")
            values.append(payload.name.strip())
        if payload.type is not None:
            fields.append("type = ?")
            values.append(payload.type)
        if payload.agg is not None:
            fields.append("agg = ?")
            values.append(payload.agg)
        if payload.sort_order is not None:
            fields.append("sort_order = ?")
            values.append(payload.sort_order)

        if not fields:
            raise AppError("没有需要更新的字段", 400, "empty_payload")

        values.append(column_id)
        db.execute(f"UPDATE data_columns SET {', '.join(fields)} WHERE id = ?", values)

        # 改成非数字列时，合计方式回落为 none，避免表格底部出现无意义的合计
        if payload.type is not None and payload.type != "number":
            db.execute("UPDATE data_columns SET agg = 'none' WHERE id = ?", (column_id,))

        row = db.execute("SELECT * FROM data_columns WHERE id = ?", (column_id,)).fetchone()
    return ok(dict(row))


@router.delete("/{sheet_id}/columns/{column_id}")
def delete_column(sheet_id: int, column_id: int):
    with get_db() as db:
        _sheet_or_404(db, sheet_id)
        cur = db.execute(
            "DELETE FROM data_columns WHERE id = ? AND sheet_id = ?", (column_id, sheet_id)
        )
        if cur.rowcount == 0:
            raise NotFoundError("列不存在")
        # 顺手把各行里该列的值清掉，避免删列又加同名列时旧数据串进来
        key = str(column_id)
        for row in db.execute("SELECT id, values_json FROM data_rows WHERE sheet_id = ?", (sheet_id,)).fetchall():
            values = _parse_values(row["values_json"])
            if key in values:
                values.pop(key)
                db.execute(
                    "UPDATE data_rows SET values_json = ? WHERE id = ?",
                    (json.dumps(values, ensure_ascii=False), row["id"]),
                )
        # 删列后重排 sort_order，避免出现空洞影响上下移动
        for idx, col in enumerate(_load_columns(db, sheet_id)):
            if col["sort_order"] != idx:
                db.execute("UPDATE data_columns SET sort_order = ? WHERE id = ?", (idx, col["id"]))
    return ok(True)


# ---------------- 行 ----------------

class RowPayload(BaseModel):
    values: dict = Field(default_factory=dict)


@router.post("/{sheet_id}/rows")
def create_row(sheet_id: int, payload: RowPayload):
    with get_db() as db:
        _sheet_or_404(db, sheet_id)
        columns = _load_columns(db, sheet_id)
        clean: dict[str, object] = {}
        for col in columns:
            raw = payload.values.get(str(col["id"]))
            normalized = _normalize_value(col["type"], raw)
            if normalized is not None:
                clean[str(col["id"])] = normalized
        cur = db.execute(
            "INSERT INTO data_rows (sheet_id, values_json, sort_order, created_at) VALUES (?, ?, 0, ?)",
            (sheet_id, json.dumps(clean, ensure_ascii=False), now_iso()),
        )
        row = db.execute("SELECT * FROM data_rows WHERE id = ?", (cur.lastrowid,)).fetchone()
    return ok({"id": row["id"], "values": _parse_values(row["values_json"]), "created_at": row["created_at"]})


@router.patch("/{sheet_id}/rows/{row_id}")
def update_row(sheet_id: int, row_id: int, payload: RowPayload):
    with get_db() as db:
        _sheet_or_404(db, sheet_id)
        current = db.execute(
            "SELECT * FROM data_rows WHERE id = ? AND sheet_id = ?", (row_id, sheet_id)
        ).fetchone()
        if not current:
            raise NotFoundError("记录不存在")
        columns = _load_columns(db, sheet_id)
        clean: dict[str, object] = {}
        for col in columns:
            raw = payload.values.get(str(col["id"]))
            normalized = _normalize_value(col["type"], raw)
            if normalized is not None:
                clean[str(col["id"])] = normalized
        db.execute(
            "UPDATE data_rows SET values_json = ? WHERE id = ?",
            (json.dumps(clean, ensure_ascii=False), row_id),
        )
        row = db.execute("SELECT * FROM data_rows WHERE id = ?", (row_id,)).fetchone()
    return ok({"id": row["id"], "values": _parse_values(row["values_json"]), "created_at": row["created_at"]})


@router.delete("/{sheet_id}/rows/{row_id}")
def delete_row(sheet_id: int, row_id: int):
    with get_db() as db:
        cur = db.execute("DELETE FROM data_rows WHERE id = ? AND sheet_id = ?", (row_id, sheet_id))
        if cur.rowcount == 0:
            raise NotFoundError("记录不存在")
    return ok(True)


# ---------------- CSV 导入 ----------------

class ImportPayload(BaseModel):
    text: str = Field(min_length=1, max_length=200000)


@router.post("/{sheet_id}/import")
def import_csv(sheet_id: int, payload: ImportPayload):
    with get_db() as db:
        _sheet_or_404(db, sheet_id)
        columns = _load_columns(db, sheet_id)
        if not columns:
            raise AppError("这张表还没有列，先加列再导入", 400, "no_columns")

        reader = csv.reader(io.StringIO(payload.text.strip()))
        raw_rows = [r for r in reader if any(cell.strip() for cell in r)]
        if not raw_rows:
            raise AppError("没有可导入的内容", 400, "empty_csv")

        # 首行如果不像数据（含该列名），就当表头跳过
        first = [c.strip() for c in raw_rows[0]]
        if first and first[0] == columns[0]["name"]:
            raw_rows = raw_rows[1:]

        imported = 0
        for line_no, cells in enumerate(raw_rows, start=1):
            if len(cells) != len(columns):
                raise AppError(
                    f"第 {line_no} 行有 {len(cells)} 个字段，当前表有 {len(columns)} 列，数量不一致",
                    400,
                    "column_mismatch",
                )
            clean: dict[str, object] = {}
            for col, cell in zip(columns, cells):
                normalized = _normalize_value(col["type"], cell)
                if normalized is not None:
                    clean[str(col["id"])] = normalized
            db.execute(
                "INSERT INTO data_rows (sheet_id, values_json, sort_order, created_at) VALUES (?, ?, 0, ?)",
                (sheet_id, json.dumps(clean, ensure_ascii=False), now_iso()),
            )
            imported += 1

    return ok({"imported": imported})
