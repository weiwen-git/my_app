# 个人工作台 — 站点规格（site-setup）

> 版本：**v3.1** ｜ 更新日期：2026-10-17 ｜ 状态：已通过设计走查，可进入开发
>
> **v3.1 变更**：完成一次全流程走查（见 `review-walkthrough-v3.0.md`），修正 20 处问题。主要：工作清单取消手动新增；顺延保留原始日期；全部店铺视图按店分组；数据列支持单独设合计方式；新增部署与恢复脚本要求；验收基准改为 1440×900。
>
> 历史：v1.1 Element Plus ｜ v1.2 多页后台 ｜ v2.0 删工作台 + 三周期 + 店铺 ｜ v3.0 六模块 9 张表

---

## 1. 需求来源（用户原话）

| 编号 | 原始表述 | 含义 |
|---|---|---|
| R1 | 「部署到我的云端服务器」 | 公网可访问 |
| R2 | 「每天重复的待办任务」 | 周期工作 |
| R3 | 「还有数据记录」 | 数据录入 |
| R6 | 「手动填 / 粘 CSV」 | 不做接口同步 |
| R7 | 「已有云服务器（Linux）」 | 可 SSH |
| R8 | 「只给我一个人使用」 | 单用户 |
| R9 | 「需要添加登录系统」 | 登录必做 |
| R10 | 「element 的管理系统界面」 | Element Plus |
| R11 | 「不需要多花俏」 | 实用优先 |
| R15 | 「不要工作台，直接进待办清单」 | 无仪表盘 |
| R16 | 「每日、每周、每月的」 | 三周期 |
| R17 | 「分不同的店铺」 | 店铺维度 |
| R22 | 「快捷入口删除」 | 该模块已删除 |
| R23 | 侧边栏「工作清单、数据、待办、便签、笔记、翻译」 | 6 项定稿 |
| R24 | 「数据里可自定义数据列的子 item」 | 多表 + 自定义列 |
| R25 | 「工作清单就是刚说的待办只是改名；待办是我突然接到的、不属于店铺的」 | 两模块分工 |
| R26 | 翻译「先做界面占位」 | 不接 API |
| R27 | 便签卡片墙 / 笔记长文 | 形态不同 |
| R28 | 店铺保留但不设菜单 | 入口在工作清单页 |
| **R29** | 走查决策：临时任务**全部进待办** | 工作清单只由模板生成 |
| **R30** | 走查决策：**不加「仅工作日」**，每日就是每天 | 周六日也出待办 |
| **R31** | 走查决策：翻译**保留占位页** | 菜单保持 6 项 |
| **R32** | 走查决策：数据合计**每列单独设** | sum / avg / none |

---

## 2. 一句话定义

**单用户 Element Plus 管理后台：左侧 6 个模块，登录后直接进「工作清单」（按店铺与每日/每周/每月管理固定工作），临时任务走「待办」，数据是可自定义列的多张表。**

---

## 2.1 单用户假设

无 `users` 表、无注册、无找回密码、无角色权限。账号密码来自 `.env`，Session 存服务端内存。
⚠️ **单用户 ≠ 无鉴权**：所有 `/api/*` 必须校验。

---

## 3. 核心概念区分

| 概念 | 定义 | 店铺 | 周期 | 能否手动新增 |
|---|---|---|---|---|
| **工作清单** | 固定重复的工作 | ✅ | ✅ | ❌ **只能由模板生成**（R29） |
| **待办** | 临时接到的、不属于店铺的事 | ❌ | ❌ | ✅ 手动录入 |
| **数据** | 自定义列的数据表 | ❌ | 由列语义决定 | ✅ |
| **便签** | 短内容卡片墙 | ❌ | ❌ | ✅ |
| **笔记** | 标题 + 长正文 | ❌ | ❌ | ✅ |
| **翻译** | 中英互译 | ❌ | ❌ | — |

**边界原则**：固定重复 + 属店铺 → 建模板，进工作清单。一次性的 → 进待办（标题里写清是哪个店）。

---

## 4. 功能范围

### P0 — 第一批（可日常使用）

| 模块 | 功能 |
|---|---|
| 登录 | 用户名 + 密码，5 次失败锁 10 分钟 |
| 工作清单 | 店铺 Tab + 周期 Tab；**只读式勾选完成**，不提供手动新增；未完成带入并标记 |
| 模板管理 | 模板 CRUD；保存后立即补生成当天实例 |
| 待办 | 临时任务列表；新增、完成、删除；优先级、截止日 |
| 数据 | 多数据表；自定义列（含每列合计方式）；行增删改；粘 CSV |

### P1 — 第二批

| 模块 | 功能 |
|---|---|
| 便签 | 卡片墙，五色，置顶 |
| 笔记 | 列表 + 长文编辑，自动保存，可搜索，可删除 |

### P2 — 第三批

| 模块 | 功能 |
|---|---|
| 翻译 | 界面占位，中英互译输入框，按钮提示「待接入」（R31：菜单保留） |

### 明确不做

- ❌ 多用户、权限、注册、找回密码
- ❌ 快捷入口、周报快照、系统信息（均不在侧边栏）
- ❌ 工作清单手动新增（R29）
- ❌ 「仅工作日」周期规则（R30）
- ❌ 移动端适配、图表库、暗色主题、消息推送
- ❌ 富文本编辑器（笔记用纯文本）
- ❌ 自定义主题、动画、视觉打磨

---

## 5. 侧边栏与页面

### 5.1 菜单（固定 6 项）

```
1. 工作清单      ← 首页
2. 数据 ▾
   ├ <各数据表，动态渲染>
   └ + 新建数据表
3. 待办
4. 便签
5. 笔记
6. 翻译
```

**基准分辨率：1440 × 900 一屏不滚动**（1920 下更宽松）。超出时卡片或表格内部独立滚动，页面级不滚。

### 5.2 工作清单页（首页）

```
工作清单                        [今天 10-17]  [管理模板]
[全部] [ICBU 主店] [1688 店] [独立站] [⚙]
┌──────────────────────────────────────────────────┐
│ 每日 4 │ 每周 2 │ 每月 1                          │
├──────────────────────────────────────────────────┤
│ ⚠ 逾期 2 项（常驻展开）                          │
│   ☐ 发布 3 个新品   [逾期 9 天]   完成  放弃     │
├──────────────────────────────────────────────────┤
│ ICBU 主店 5                                      │  ← 仅在「全部」视图
│ ☑ 查看昨日询盘                          删除     │
│ ☐ 回复所有未读消息                      删除     │
├──────────────────────────────────────────────────┤
│ 1688 店 3                                        │
│ ☐ 更新橱窗产品                          删除     │
└──────────────────────────────────────────────────┘
今日 3/7 已完成
```

**修正后的规则**：
- **无「+ 新增今日工作」按钮**，工作清单只由模板生成（R29）
- **「全部店铺」视图按店铺分组**，每组一个小标题（店名 + 未完成数）
- **具体店铺视图平铺**，不分组，不显示店铺标签
- **逾期区常驻展开**（有逾期时才出现），标题「⚠ 逾期 N 项」
- 周期 Tab 角标：选「全部」= 各店合计；选单店 = 该店数量
- 空态引导（首次使用）：
  `① 添加店铺 → ② 建工作清单模板 → ③ 明天自动出现`
  引导里直接放按钮，店铺入口在空态里**显式呈现**，不靠齿轮

### 5.3 待办页

```
待办                                    [+ 新增待办]
┌──────────────────────────────────────────────────┐
│ ☐ 给张总回个电话  [高]  10-18截止      完成 删除 │
│ ☐ 整理展会样品清单                     完成 删除 │
└──────────────────────────────────────────────────┘
[ 已完成 3 项 ▾ ]
```

- 无店铺、无周期
- 字段：标题（必填）、备注、优先级（低/普通/高）、截止日（可空）
- 截止日已过且未完成 → 日期标红

### 5.4 数据页

```
ICBU 周数据                    [管理列] [+ 新增记录] [粘贴 CSV]
┌────────────────────────────────────────────────────────┐
│ 周起始日      │ 询盘 │ 曝光  │ 点击 │ 转化率 │ 备注     │
│ 10-12~10-18   │  42  │ 8,240 │ 316  │ 3.2%   │ 新客     │
│ ...                                                    │
│ 合计 / 均值   │ 115  │24,646 │ 880  │ 3.5%   │          │
└────────────────────────────────────────────────────────┘
```

- 列类型：`number` / `text` / `date`
- **每列可设合计方式**（R32）：`sum` 求和 / `avg` 平均 / `none` 不合计
- 底部合计行按各列自己的规则显示；`text`/`date` 列留空
- **记录按 `created_at` 倒序**（最新在上）
- 列较多时表格内部横向滚动，页面不滚
- 同一表内**列名唯一**，重名时创建失败并提示

### 5.5 便签页

五色卡片墙（`column-count` 多列）。点击内联编辑，失焦保存。
**删除策略**：原本有内容后被清空才删除；新建后从未输入的空卡片保留，不自动删。

### 5.6 笔记页

左侧列表（标题 + 时间 + 删除按钮）+ 右侧编辑区（标题 + 正文 textarea）。失焦或 2 秒防抖自动保存。顶部搜索按标题过滤。

### 5.7 翻译页

左右输入区 + 交换按钮，中↔英。点「翻译」提示「翻译接口待接入」，**不发起任何请求**。页面明确标注「功能开发中」。

### 5.8 路由表

| 路由 | 页面 |
|---|---|
| `/login` | 登录 |
| `/` | 重定向 `/worklist` |
| `/worklist` | 工作清单（首页） |
| `/worklist/templates` | 模板管理 |
| `/data/:sheetId` | 数据表详情 |
| `/todos` | 待办 |
| `/sticky` | 便签 |
| `/notes` | 笔记列表 |
| `/notes/:id` | 笔记详情 |
| `/translate` | 翻译 |

店铺管理、模板表单、列管理、新建数据表 —— 全部用 `el-dialog`，不占路由。
**删除数据表后**：跳第一张表；一张都没有则显示空态，不留在失效路由。

---

## 6. 数据模型（9 张表）

```sql
CREATE TABLE shops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  short_name TEXT DEFAULT '',
  sort_order INTEGER DEFAULT 0,
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  shop_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  repeat_rule TEXT NOT NULL,        -- daily | weekly:1-7 | monthly:1-31
  sort_order INTEGER DEFAULT 0,
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_instances (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_id INTEGER,
  shop_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  period_type TEXT NOT NULL,
  task_date TEXT NOT NULL,          -- 当前归属日期
  origin_date TEXT NOT NULL,        -- ★v3.1 首次生成日期，用于历史统计
  status TEXT DEFAULT 'todo',
  carried INTEGER DEFAULT 0,
  note TEXT DEFAULT '',
  done_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE todos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  note TEXT DEFAULT '',
  priority TEXT DEFAULT 'normal',   -- low | normal | high
  due_date TEXT,
  status TEXT DEFAULT 'todo',
  done_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sticky_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT NOT NULL,
  color TEXT DEFAULT 'yellow',
  pinned INTEGER DEFAULT 0,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT
);

CREATE TABLE notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT
);

CREATE TABLE data_sheets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  sort_order INTEGER DEFAULT 0,
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE data_columns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sheet_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  type TEXT DEFAULT 'number',       -- number | text | date
  agg TEXT DEFAULT 'sum',           -- ★v3.1 sum | avg | none
  sort_order INTEGER DEFAULT 0,
  FOREIGN KEY (sheet_id) REFERENCES data_sheets(id)
);

CREATE TABLE data_rows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sheet_id INTEGER NOT NULL,
  values_json TEXT NOT NULL DEFAULT '{}',
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (sheet_id) REFERENCES data_sheets(id)
);
```

---

## 7. 关键业务规则

### 7.1 生成

| 周期 | `repeat_rule` | 时机 |
|---|---|---|
| 每日 | `daily` | **每天（含周六日）** |
| 每周 | `weekly:1`~`weekly:7` | 指定周几 |
| 每月 | `monthly:1`~`monthly:31` | 指定几号；**当月无该日取最后一天** |

- 打开工作清单时生成，**接口幂等**
- **保存模板后立即补生成当天实例**（若匹配今天），并提示「已加入今日清单」
- 停用店铺 / 停用模板不生成

### 7.2 顺延

- 未完成次日带入：**更新 `task_date` + `carried+1`**，`origin_date` 不变
- 上限 7 天，达到后进逾期区，**逾期区常驻展开**
- 历史视图按 `origin_date` 统计：「该日原有 X 项，其中 Y 项已顺延至今日」

### 7.3 其他

| 规则 | 定义 |
|---|---|
| 数据合计 | 按每列 `agg` 计算：sum 求和 / avg 平均 / none 不显示 |
| 列名 | 同一表内唯一 |
| 改列类型为 number | 校验已有值全部可转数字，否则拒绝 |
| 删列 | 二次确认 + 提示「该列数据将一并删除」 |
| CSV 粘贴 | 按当前列顺序解析，字段数不符整体拒绝并报行号 |
| 停用店铺 | 历史实例保留，店铺标签置灰显示 |
| 店铺删除 | 不提供真删，只能停用 |

---

## 8. 安全与前端容错

- [ ] 所有 `/api/*` 校验登录态，未登录 401
- [ ] 账号密码仅从环境变量读取
- [ ] Cookie `HttpOnly` + `SameSite=Lax` + 生产 `Secure`
- [ ] 公网仅开 443
- [ ] **`api.js` 统一拦截 401**：清登录态 → 跳 `/login`，不白屏
- [ ] 无 `users` 表、无注册接口

---

## 9. 项目结构

```
project/
├── backend/app/
│   ├── main.py  db.py  auth.py
│   └── routers/  auth.py tasks.py shops.py todos.py
│                 sticky.py notes.py sheets.py
├── backend/scripts/
│   ├── seed.py
│   ├── make-password.py     # ★v3.1 生成 bcrypt 哈希
│   └── restore.sh           # ★v3.1 备份恢复
├── frontend/src/
│   ├── main.js  App.vue  api.js  auth.js  router.js  style.css
│   ├── layout/AdminLayout.vue
│   └── views/  Login WorkList TemplateManage DataSheet
│                TodoList StickyBoard NoteList NoteDetail Translate
├── Dockerfile  docker-compose.yml  .dockerignore  .env.example
```

---

## 10. 部署与运维（v3.1 补充）

| 项 | 要求 |
|---|---|
| 密码生成 | 运行 `python scripts/make-password.py`，把输出贴进 `.env` 的 `WB_PASSWORD_HASH` |
| 目录权限 | 宿主机执行 `chown -R 1000:1000 data backups`，否则容器内 SQLite 写入失败 |
| 首次启动 | `data/` 为空时自动建表，无需手动迁移 |
| 备份 | cron `0 3 * * *`，保留 14 份 |
| **恢复** | 停容器 → 用备份覆盖 `data/workbench.db` → 起容器；`scripts/restore.sh` 封装此流程 |
| 时区 | 容器与代码均固定 `Asia/Shanghai` |

---

## 11. 待确认

| 项 | 阻塞什么 |
|---|---|
| 店铺清单 | 不阻塞，先用示例 |
| 工作清单内容 | 不阻塞，可先空着 |
| 数据表与列 | 不阻塞，界面里自己加 |
| 域名 | 部署前 |

---

## 12. 走查修正记录（20 项）

| 编号 | 问题 | 处理 | 类型 |
|---|---|---|---|
| C1 | 临时任务归属冲突 | 工作清单去掉手动新增，全部进待办 | ✅ 已采纳 |
| C2 | 顺延抹掉历史 | 加 `origin_date` | ✅ 已采纳 |
| C3 | 全部视图一锅粥 | 按店铺分组 | ✅ 已采纳 |
| C4 | 数字列全求和会算错 | 加 `agg` 字段 | ✅ 已采纳 |
| C5 | 翻译菜单是死的 | **保留占位页**（用户决定） | ⚠️ 不修改 |
| U1 | 首屏空白不知道干嘛 | 空态三步引导 + 显式店铺入口 | ✅ 已采纳 |
| U2 | 新建模板当天不出现 | 保存后补生成 | ✅ 已采纳 |
| U3 | 没有仅工作日 | **不加**（用户决定） | ⚠️ 不修改 |
| U4 | 便签空卡片被删 | 改为"清空才删" | ✅ 已采纳 |
| U5 | 1920 基准不现实 | 改 1440×900 | ✅ 已采纳 |
| U6 | 列名可重名 | 同表内唯一 | ✅ 已采纳 |
| U7 | 逾期区无限堆积 | 常驻展开 | ✅ 已采纳 |
| U8 | 数据无排序依据 | 按创建时间倒序 | ✅ 已采纳 |
| G1 | 密码哈希不会生成 | 加 `make-password.py` | ✅ 已采纳 |
| G2 | 备份不会恢复 | 加 `restore.sh` + 步骤 | ✅ 已采纳 |
| G3 | 401 白屏 | `api.js` 统一拦截 | ✅ 已采纳 |
| G4 | 删表后路由失效 | 跳第一张表或空态 | ✅ 已采纳 |
| G5 | 目录权限导致写失败 | 部署加 `chown` | ✅ 已采纳 |
| G6 | 笔记不能删 | 列表加删除 | ✅ 已采纳 |
| G7 | 停用店铺标签显示 | 保留并置灰 | ✅ 已采纳 |
| G8 | 角标含义不明 | 全部=合计，单店=本店 | ✅ 已采纳 |

**采纳 18 项，用户保留 2 项（C5 翻译占位、U3 不加工作日规则）。**

---

## 13. 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-17 | 原生 JS 单页 |
| v1.1 | 2026-10-17 | Vue3 + Element Plus + Vite |
| v1.2 | 2026-10-17 | 完整多页后台 |
| v2.0 | 2026-10-17 | 删工作台；三周期；店铺维度 |
| v3.0 | 2026-10-17 | 6 模块；9 张表 |
| **v3.1** | 2026-10-17 | **设计走查后修正 18 项；新增 origin_date、agg 字段；部署与恢复脚本** |
