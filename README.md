# 个人工作台

单用户 Web 工作台，部署在自己的服务器上。侧边栏 6 个模块：工作清单 / 数据 / 待办 / 便签 / 笔记 / 翻译。

**当前状态**：6 个模块全部可用（翻译为界面占位，按 PRD 第三批实现）。

## 目录

```
my_app/
├── backend/            FastAPI + SQLite
│   ├── app/
│   │   ├── config.py       环境变量集中校验
│   │   ├── errors.py       统一 {ok,data,error} + 类型化异常
│   │   ├── db.py           9 张表、WAL、时区、时间工具
│   │   ├── auth.py         内存 Session + bcrypt + 登录锁定
│   │   └── routers/        auth shops tasks todos sticky notes sheets
│   ├── scripts/
│   │   ├── seed.py           示例数据 / --force 完全重置
│   │   └── make-password.py  生成 bcrypt 哈希
│   └── requirements.txt
├── frontend/           Vue3 + Element Plus + Vite
│   └── src/
│       ├── api.js           fetch 封装 + 401 统一跳登录
│       ├── auth.js          模块级登录态（不用 Pinia）
│       ├── router.js        路由表 + 登录守卫
│       ├── layout/          AdminLayout（侧边栏 + 面包屑）
│       └── views/           各模块页面
├── .e2e/               端到端自测脚本（Playwright + 系统 Chrome）
├── data/               SQLite（运行时生成，不入库）
└── backups/
```

## 本地启动

### 后端

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows
pip install -r requirements.txt
cp .env.example .env

python scripts/seed.py          # 灌示例数据（3 店铺 / 13 模板 / 3 数据表）
uvicorn app.main:app --reload --port 8000
```

后端 http://127.0.0.1:8000 ，接口文档 `/docs` 。

### 前端

```bash
cd frontend
npm install
npm run dev                     # 若报 'vite' 不是内部命令，见下方说明
```

打开 http://127.0.0.1:5173 （用 IP，不要用 localhost，vite 只监听 IPv4）。

> 本机 PATH 可能没有 `node_modules/.bin`，导致 `npm run dev` 找不到 vite。直接用：
> `node node_modules/vite/bin/vite.js --port 5173`

### 登录

| 项 | 值 |
|---|---|
| 用户名 | `weiwen` |
| 密码 | `admin123` |

来自 `backend/.env` 的 `WB_PASSWORD`（明文，仅开发）。上线前改用哈希：

```bash
python scripts/make-password.py   # 输出 WB_PASSWORD_HASH=...
```

写入 `.env` 后清空 `WB_PASSWORD`，重启生效。

## 接口一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| POST/POST/GET | `/api/auth/login` `logout` `me` | 登录态 |
| GET/POST/PATCH | `/api/shops` | 店铺（只能停用，不能删） |
| POST | `/api/tasks/generate` | 生成当天清单（幂等） |
| GET | `/api/tasks` | 按 日期+店铺+周期 取清单 |
| PATCH/DELETE/POST | `/api/tasks/{id}/toggle` `{id}` `{id}/abandon` | 勾选 / 删除 / 放弃逾期 |
| GET/POST/PATCH | `/api/templates` `/list` `/{id}` | 工作清单模板 |
| GET/POST | `/api/sheets` | 数据表列表 / 新建 |
| GET/PATCH/DELETE | `/api/sheets/{id}` | 详情（含列与行）/ 改名 / 停用 |
| POST/PATCH/DELETE | `/api/sheets/{id}/columns[/{cid}]` | 列增删改 |
| POST/PATCH/DELETE | `/api/sheets/{id}/rows[/{rid}]` | 行增删改 |
| POST | `/api/sheets/{id}/import` | 粘贴 CSV 导入 |
| GET/POST/PATCH/DELETE | `/api/todos[/{id}]` | 待办 |
| GET/POST/PATCH/DELETE | `/api/sticky[/{id}]` | 便签 |
| GET/POST/PATCH/DELETE | `/api/notes[/{id}]` | 笔记 |

## 关键规则（改代码前必读）

1. **时区固定 `Asia/Shanghai`**。所有"今天"按北京时间算；SQLite 的 `created_at` 用 `datetime('now','+8 hours')`，因为默认 `CURRENT_TIMESTAMP` 是 UTC。
2. **生成接口幂等**：`(template_id, task_date)` 已存在则跳过。
3. **「每月 31 号」在 2 月落到当月最后一天**，否则该任务永远不出现。
4. **顺延是更新 `task_date`**，`origin_date` 保留首次生成日；`carried` 按日期差累加，满 7 天进逾期区。
5. **工作清单不提供手动新增**，临时的事走「待办」。
6. **店铺只能停用，不能删除**，否则历史条目变孤儿。
7. **数据行用 `values_json` 存值**，因为列完全自定义 —— 这是"加列不改表结构"的前提。
8. **数字列的合计按列配置**（sum / avg / none），转化率这类列必须设 avg，否则会算出无意义的和。

## 端到端自测

用系统 Chrome（无需下载 Chromium）：

```bash
node .e2e/walkthrough.cjs   # 第一批：登录 → 清单 → 店铺 → 数据总览（18 项）
node .e2e/modules.cjs       # 第二批：模板/待办/便签/笔记/数据表/翻译（14 项）
```

截图分别输出到 `.e2e/shots/` 和 `.e2e/shots2/`。

**注意**：每次跑完会产生测试数据，用 `python backend/scripts/seed.py --force` 清理（会清空所有业务数据，重新灌种子）。

## 下一步

- 第三批：翻译接入实际 API
- 部署：Dockerfile 多阶段构建 + Nginx + 每日备份
