"""种子数据：3 个店铺 + 12 条工作清单模板 + 3 张数据表。

可重复执行：若 shops 已有数据则跳过，加 --force 会清空后重建（仅开发用）。
用法：python backend/scripts/seed.py [--force]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402
from app.db import get_db, init_db  # noqa: E402

SHOPS = [
    ("ICBU 主店", "主店", 0),
    ("1688 店", "1688", 1),
    ("独立站", "独立站", 2),
]

TEMPLATES = {
    "ICBU 主店": [
        ("查看昨日询盘", "daily", 0),
        ("回复所有未读消息", "daily", 1),
        ("跟进 RFQ 高优先报价", "daily", 2),
        ("检查 P4P 消耗与出价", "daily", 3),
        ("导出上周数据并录入", "weekly:1", 0),
        ("更新橱窗产品", "weekly:3", 1),
        ("月度报表整理", "monthly:1", 0),
        ("检查关键词排名", "monthly:15", 1),
    ],
    "1688 店": [
        ("回复旺旺留言", "daily", 0),
        ("更新橱窗产品", "weekly:2", 0),
        ("月度对账", "monthly:5", 0),
    ],
    "独立站": [
        ("检查订单与发货", "daily", 0),
        ("更新产品图", "weekly:4", 0),
    ],
}

SHEETS = [
    (
        "ICBU 周数据",
        [
            ("周起始日", "date", "none"),
            ("询盘", "number", "sum"),
            ("曝光", "number", "sum"),
            ("点击", "number", "sum"),
            ("转化率", "number", "avg"),
            ("备注", "text", "none"),
        ],
    ),
    (
        "1688 周数据",
        [
            ("周起始日", "date", "none"),
            ("访客", "number", "sum"),
            ("咨询", "number", "sum"),
            ("成交单数", "number", "sum"),
            ("成交额", "number", "sum"),
        ],
    ),
    (
        "广告消耗",
        [
            ("日期", "date", "none"),
            ("平台", "text", "none"),
            ("消耗", "number", "sum"),
            ("点击", "number", "sum"),
        ],
    ),
]


def main() -> None:
    force = "--force" in sys.argv
    config.validate()
    init_db()

    with get_db() as db:
        existing = db.execute("SELECT COUNT(*) AS n FROM shops").fetchone()["n"]
        if existing and not force:
            print(f"[skip] 已有 {existing} 个店铺，未做任何修改。要重建请加 --force")
            return

        if force:
            # 完全重置：包含内容类表，避免测试数据残留
            for table in (
                "task_instances",
                "task_templates",
                "shops",
                "data_rows",
                "data_columns",
                "data_sheets",
                "todos",
                "sticky_notes",
                "notes",
            ):
                db.execute(f"DELETE FROM {table}")
            print("[reset] 已清空全部业务数据（店铺/模板/清单/数据表/待办/便签/笔记）")

        shop_ids: dict[str, int] = {}
        for name, short, order in SHOPS:
            cur = db.execute(
                "INSERT INTO shops (name, short_name, sort_order, active) VALUES (?, ?, ?, 1)",
                (name, short, order),
            )
            shop_ids[name] = cur.lastrowid

        tpl_count = 0
        for shop_name, items in TEMPLATES.items():
            for title, rule, order in items:
                db.execute(
                    "INSERT INTO task_templates (shop_id, title, repeat_rule, sort_order, active) "
                    "VALUES (?, ?, ?, ?, 1)",
                    (shop_ids[shop_name], title, rule, order),
                )
                tpl_count += 1

        sheet_count = 0
        for sheet_name, columns in SHEETS:
            cur = db.execute("INSERT INTO data_sheets (name, sort_order, active) VALUES (?, ?, 1)", (sheet_name, sheet_count))
            sheet_id = cur.lastrowid
            for idx, (col_name, col_type, agg) in enumerate(columns):
                db.execute(
                    "INSERT INTO data_columns (sheet_id, name, type, agg, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (sheet_id, col_name, col_type, agg, idx),
                )
            sheet_count += 1

    print(f"[done] 店铺 {len(SHOPS)} / 模板 {tpl_count} / 数据表 {sheet_count}")
    print(f"[db]   {config.DB_PATH}")


if __name__ == "__main__":
    main()
