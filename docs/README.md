# 项目文档

这个目录存放需求与技术文档，与代码一起版本管理。**先看 PRD，再看技术规格，改代码时查规则。**

| 文档 | 给谁看 | 什么时候看 |
|---|---|---|
| [PRD.md](./PRD.md) | 产品视角 | 定需求、验收。含 9 个功能模块（F-01~F-09）与验收编号（AC-xx-x） |
| [site-setup.md](./site-setup.md) | 开发 | 写代码时查字段定义、数据模型、业务规则原文 |
| [review-walkthrough.md](./review-walkthrough.md) | 想了解设计取舍时 | 记录了上线前的 20 项走查问题及处理方式 |
| [tasklist.md](./tasklist.md) | 排期/跟进度 | 28 个开发任务，分 A–H 八个阶段 |

## 阅读顺序

1. **PRD.md** —— 搞清楚要做什么、不做什么
2. **site-setup.md** §6 数据模型 —— 9 张表的字段
3. **site-setup.md** §7 关键业务规则 —— 周期生成、顺延、合计方式
4. **review-walkthrough.md** —— 理解"为什么这么设计"，避免改回老问题

## 与代码的对应

| 文档章节 | 代码位置 |
|---|---|
| 数据模型（9 张表） | `backend/app/db.py` 里的 `SCHEMA` |
| 业务规则（周期/顺延） | `backend/app/routers/tasks.py` 的 `_matches` / `_carry_over` |
| 数据合计方式 | `backend/app/routers/sheets.py` 的 `agg` 字段 + 前端 `DataSheet.vue` 的 `columnTotal` |
| 路由表 | `frontend/src/router.js` |
| UI 规范 | `frontend/src/style.css` + 各页面 scoped 样式 |

## 注意

- 文档里的路径写的是 `ai/memory-bank/xxx`（原始工作目录），在本仓库中对应 `docs/xxx`。
- 文档版本停在 v3.1 / PRD v1.0，与当前代码一致。后续改动请同步更新这两份。
