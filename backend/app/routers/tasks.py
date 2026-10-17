"""工作清单：模板、条目生成、顺延、逾期。

两条规则最容易出错，这里集中在 _matches / _carry_over：
1. 「每月 31 号」在 2 月要落在最后一天，否则该任务永远不出现。
2. 顺延是更新 task_date，不是新建记录；origin_date 保留首次生成日。
"""

from __future__ import annotations

from datetime import date as Date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from .. import auth, config
from ..db import d, get_db, now_iso, last_day_of_month, today
from ..errors import AppError, NotFoundError, ok

router = APIRouter(prefix="/api/tasks", tags=["tasks"], dependencies=[Depends(auth.require_auth)])

PERIODS = ("daily", "weekly", "monthly")

# 模板单独一个前缀。若挂在 /api/tasks/templates 下，会被 /api/tasks/{task_id}/toggle
# 的 int 参数抢先匹配，"templates" 转 int 失败直接 422。
router_tpl = APIRouter(prefix="/api/templates", tags=["templates"], dependencies=[Depends(auth.require_auth)])


# ---------------- 规则解析 ----------------

def _matches(rule: str, day: Date) -> tuple[bool, str]:
    """判断模板今天是否该生成。返回 (是否匹配, 周期类型)。"""
    rule = (rule or "").strip()
    if rule == "daily":
        return True, "daily"

    if rule.startswith("weekly:"):
        try:
            n = int(rule.split(":", 1)[1])
        except ValueError:
            return False, "weekly"
        return day.isoweekday() == n, "weekly"

    if rule.startswith("monthly:"):
        try:
            n = int(rule.split(":", 1)[1])
        except ValueError:
            return False, "monthly"
        last = last_day_of_month(day)
        target = n if n <= last else last  # 31 号在 2 月落到 28/29 号
        return day.day == target, "monthly"

    return False, "daily"


def _carry_over(db, day: Date) -> int:
    """把之前所有未完成、未超限的条目带到今天。返回带走条数。

    按日期差累加 carried，因此跳过几天不用也不会漏带，
    也不会把"隔了 3 天"算成"顺延 1 天"。
    """
    today_s = d(day)
    rows = db.execute(
        "SELECT id, task_date, carried FROM task_instances "
        "WHERE status = 'todo' AND task_date < ? AND carried < ?",
        (today_s, config.MAX_CARRY_DAYS),
    ).fetchall()

    moved = 0
    for row in rows:
        gap = (day - Date.fromisoformat(row["task_date"])).days
        new_carried = row["carried"] + max(gap, 1)
        if new_carried > config.MAX_CARRY_DAYS:
            continue  # 超限的不动，留在原日期，由逾期区展示
        db.execute(
            "UPDATE task_instances SET task_date = ?, carried = ? WHERE id = ?",
            (today_s, new_carried, row["id"]),
        )
        moved += 1
    return moved


def _generate(db, day: Date) -> int:
    """生成当天条目，幂等：已存在的（模板, 日期）跳过。"""
    today_s = d(day)
    shops = db.execute("SELECT id, name FROM shops WHERE active = 1 ORDER BY sort_order, id").fetchall()
    created = 0

    for shop in shops:
        templates = db.execute(
            "SELECT * FROM task_templates WHERE shop_id = ? AND active = 1 ORDER BY sort_order, id",
            (shop["id"],),
        ).fetchall()
        for tpl in templates:
            matched, period = _matches(tpl["repeat_rule"], day)
            if not matched:
                continue
            exists = db.execute(
                "SELECT 1 FROM task_instances WHERE template_id = ? AND task_date = ?",
                (tpl["id"], today_s),
            ).fetchone()
            if exists:
                continue
            db.execute(
                "INSERT INTO task_instances "
                "(template_id, shop_id, title, period_type, task_date, origin_date, status, carried, note) "
                "VALUES (?, ?, ?, ?, ?, ?, 'todo', 0, '')",
                (tpl["id"], shop["id"], tpl["title"], period, today_s, today_s),
            )
            created += 1
    return created


def _row_to_item(row) -> dict:
    return {
        "id": row["id"],
        "template_id": row["template_id"],
        "shop_id": row["shop_id"],
        "shop_name": row["shop_name"] if "shop_name" in row.keys() else "",
        "title": row["title"],
        "period_type": row["period_type"],
        "task_date": row["task_date"],
        "origin_date": row["origin_date"],
        "status": row["status"],
        "carried": row["carried"],
        "done_at": row["done_at"],
    }


# ---------------- 接口 ----------------

@router.post("/generate")
def generate(day: str | None = Query(default=None, alias="date")):
    target = Date.fromisoformat(day) if day else today()
    with get_db() as db:
        moved = _carry_over(db, target)
        created = _generate(db, target)
    return ok({"date": d(target), "created": created, "carried": moved})


@router.get("")
def list_tasks(
    day: str | None = Query(default=None, alias="date"),
    shop_id: str = Query(default="all"),
    period: str = Query(default="daily"),
):
    target = Date.fromisoformat(day) if day else today()
    target_s = d(target)
    if period not in PERIODS:
        raise AppError("周期参数不合法", 400, "bad_period")

    shop_filter = ""
    params: list = [target_s, period]
    if shop_id != "all":
        try:
            sid = int(shop_id)
        except ValueError:
            raise AppError("店铺参数不合法", 400, "bad_shop")
        shop_filter = " AND t.shop_id = ?"
        params.append(sid)

    base = (
        "SELECT t.*, s.name AS shop_name FROM task_instances t "
        "LEFT JOIN shops s ON s.id = t.shop_id "
        "WHERE t.task_date = ? AND t.period_type = ?" + shop_filter
    )

    with get_db() as db:
        rows = db.execute(base + " ORDER BY s.sort_order, t.id", params).fetchall()
        items = [_row_to_item(r) for r in rows]

        # 各周期未完成数量（受店铺筛选影响）
        count_params: list = [target_s]
        count_sql = (
            "SELECT period_type, COUNT(*) AS n FROM task_instances "
            "WHERE task_date = ? AND status = 'todo'"
        )
        if shop_id != "all":
            count_sql += " AND shop_id = ?"
            count_params.append(sid)
        counts = {p: 0 for p in PERIODS}
        for r in db.execute(count_sql + " GROUP BY period_type", count_params).fetchall():
            counts[r["period_type"]] = r["n"]

        # 当日完成进度（当前周期 + 店铺筛选）
        prog_row = db.execute(
            "SELECT SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) AS done, COUNT(*) AS total "
            "FROM task_instances WHERE task_date = ? AND period_type = ?" + shop_filter.replace("t.", ""),
            params,
        ).fetchone()

        # 逾期：早于今天、未完成、顺延已满上限
        overdue_params: list = [target_s, config.MAX_CARRY_DAYS]
        overdue_sql = (
            "SELECT t.*, s.name AS shop_name FROM task_instances t "
            "LEFT JOIN shops s ON s.id = t.shop_id "
            "WHERE t.task_date < ? AND t.status = 'todo' AND t.carried >= ?"
        )
        if shop_id != "all":
            overdue_sql += " AND t.shop_id = ?"
            overdue_params.append(sid)
        overdue = [_row_to_item(r) for r in db.execute(overdue_sql + " ORDER BY t.task_date", overdue_params)]

    groups: list[dict] = []
    seen: dict[int, dict] = {}
    for item in items:
        gid = item["shop_id"]
        if gid not in seen:
            seen[gid] = {"shop_id": gid, "shop_name": item["shop_name"], "items": []}
            groups.append(seen[gid])
        seen[gid]["items"].append(item)

    return ok(
        {
            "date": target_s,
            "is_today": target_s == d(today()),
            "shop_id": shop_id,
            "period": period,
            "items": items,
            "groups": groups,
            "overdue": overdue,
            "counts": counts,
            "progress": {
                "done": (prog_row["done"] or 0) if prog_row else 0,
                "total": (prog_row["total"] or 0) if prog_row else 0,
            },
        }
    )


@router.patch("/{task_id}/toggle")
def toggle_task(task_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM task_instances WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise NotFoundError("待办不存在")
        if row["status"] == "done":
            db.execute(
                "UPDATE task_instances SET status='todo', done_at=NULL WHERE id=?", (task_id,)
            )
            new_status = "todo"
        else:
            db.execute(
                "UPDATE task_instances SET status='done', done_at=? WHERE id=?", (now_iso(), task_id)
            )
            new_status = "done"
    return ok({"id": task_id, "status": new_status})


@router.delete("/{task_id}")
def delete_task(task_id: int):
    with get_db() as db:
        cur = db.execute("DELETE FROM task_instances WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            raise NotFoundError("待办不存在")
    return ok(True)


@router.post("/{task_id}/abandon")
def abandon_task(task_id: int):
    """放弃逾期项：标记为 done 但记 note，不再被顺延。"""
    with get_db() as db:
        cur = db.execute(
            "UPDATE task_instances SET status='done', done_at=?, note='已放弃' WHERE id = ?",
            (now_iso(), task_id),
        )
        if cur.rowcount == 0:
            raise NotFoundError("待办不存在")
    return ok(True)


# ---------------- 模板 ----------------

class TemplatePayload(BaseModel):
    shop_id: int
    title: str = Field(min_length=1, max_length=80)
    repeat_rule: str
    sort_order: int = 0


class TemplatePatch(BaseModel):
    shop_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=80)
    repeat_rule: str | None = None
    sort_order: int | None = None
    active: int | None = None


def _validate_rule(rule: str) -> str:
    rule = rule.strip()
    if rule == "daily":
        return rule
    if rule.startswith("weekly:"):
        n = int(rule.split(":", 1)[1]) if rule.split(":", 1)[1].isdigit() else 0
        if 1 <= n <= 7:
            return f"weekly:{n}"
        raise AppError("每周规则需为 weekly:1~7", 400, "bad_rule")
    if rule.startswith("monthly:"):
        n = int(rule.split(":", 1)[1]) if rule.split(":", 1)[1].isdigit() else 0
        if 1 <= n <= 31:
            return f"monthly:{n}"
        raise AppError("每月规则需为 monthly:1~31", 400, "bad_rule")
    raise AppError("重复规则不合法", 400, "bad_rule")


@router_tpl.get("/list")
def list_templates(shop_id: str = Query(default="all")):
    sql = (
        "SELECT tt.*, s.name AS shop_name FROM task_templates tt "
        "LEFT JOIN shops s ON s.id = tt.shop_id WHERE 1=1"
    )
    params: list = []
    if shop_id != "all":
        try:
            params.append(int(shop_id))
        except ValueError:
            raise AppError("店铺参数不合法", 400, "bad_shop")
        sql += " AND tt.shop_id = ?"
    sql += " ORDER BY s.sort_order, tt.sort_order, tt.id"
    with get_db() as db:
        rows = [dict(r) for r in db.execute(sql, params).fetchall()]
    return ok(rows)


@router_tpl.post("")
def create_template(payload: TemplatePayload):
    rule = _validate_rule(payload.repeat_rule)
    with get_db() as db:
        shop = db.execute("SELECT id FROM shops WHERE id = ?", (payload.shop_id,)).fetchone()
        if not shop:
            raise AppError("店铺不存在", 400, "shop_not_found")
        cur = db.execute(
            "INSERT INTO task_templates (shop_id, title, repeat_rule, sort_order, active) "
            "VALUES (?, ?, ?, ?, 1)",
            (payload.shop_id, payload.title.strip(), rule, payload.sort_order),
        )
        tpl_id = cur.lastrowid

        # 保存后立即检查今天是否匹配，匹配则补生成 —— 否则当天看不到自己刚建的东西
        created_today = 0
        day = today()
        matched, period = _matches(rule, day)
        if matched:
            exists = db.execute(
                "SELECT 1 FROM task_instances WHERE template_id = ? AND task_date = ?",
                (tpl_id, d(day)),
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO task_instances "
                    "(template_id, shop_id, title, period_type, task_date, origin_date, status, carried, note) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'todo', 0, '')",
                    (tpl_id, payload.shop_id, payload.title.strip(), period, d(day), d(day)),
                )
                created_today = 1
        row = db.execute("SELECT * FROM task_templates WHERE id = ?", (tpl_id,)).fetchone()
    return ok({"template": dict(row), "created_today": created_today})


@router_tpl.patch("/{template_id}")
def update_template(template_id: int, payload: TemplatePatch):
    fields, values = [], []
    if payload.shop_id is not None:
        fields.append("shop_id = ?")
        values.append(payload.shop_id)
    if payload.title is not None:
        fields.append("title = ?")
        values.append(payload.title.strip())
    if payload.repeat_rule is not None:
        fields.append("repeat_rule = ?")
        values.append(_validate_rule(payload.repeat_rule))
    if payload.sort_order is not None:
        fields.append("sort_order = ?")
        values.append(payload.sort_order)
    if payload.active is not None:
        fields.append("active = ?")
        values.append(payload.active)

    if not fields:
        raise AppError("没有需要更新的字段", 400, "empty_payload")

    values.append(template_id)
    with get_db() as db:
        cur = db.execute(f"UPDATE task_templates SET {', '.join(fields)} WHERE id = ?", values)
        if cur.rowcount == 0:
            raise NotFoundError("模板不存在")
        row = db.execute("SELECT * FROM task_templates WHERE id = ?", (template_id,)).fetchone()
    return ok(dict(row))
