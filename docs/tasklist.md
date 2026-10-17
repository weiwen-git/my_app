# 个人工作台 — 开发任务清单

> **版本 v3.1**（已完成设计走查，20 项修正已并入，见规格 §12）

**项目代号**：`personal-workbench`
**规格文档**：`ai/memory-bank/site-setup.md`（以该文档为准）
**走查报告**：`ai/memory-bank/review-walkthrough-v3.0.md`
**使用对象**：仅 weiwen 本人（单用户）
**技术栈**：Vue3 + vue-router + Element Plus + Vite ｜ FastAPI + SQLite ｜ Docker 多阶段 + Nginx
**侧边栏**：工作清单 / 数据 / 待办 / 便签 / 笔记 / 翻译（固定 6 项）
**验收基准**：**1440 × 900 一屏不滚动**

---

## 走查修正速查（开发时对照，避免按旧设计做）

| 修正 | 落在哪个任务 | 要点 |
|---|---|---|
| 工作清单不提供手动新增 | T6 / T8 | 只由模板生成，临时事全进待办 |
| 顺延保留 `origin_date` | T2 / T7 | 改 date 不改 origin |
| 全部店铺视图按店分组 | T6 | 单店视图才平铺 |
| 数据列 `agg`（sum/avg/none） | T2 / T16 | 合计按列各自规则 |
| 空白首屏三步引导 | T6 | 店铺入口显式呈现，不靠齿轮 |
| 保存模板后补生成 | T11 | 否则当天看不到 |
| 便签"清空才删" | T19 | 新建空卡片不删 |
| 列名同表唯一 | T16 | 重名拒绝 |
| 逾期区常驻展开 | T9 | 有逾期就展开 |
| 数据按创建时间倒序 | T15 | 最新在上 |
| 密码哈希生成脚本 | T24 | `make-password.py` |
| 备份恢复脚本 | T27 | `restore.sh` |
| 401 统一跳登录 | T4 | `api.js` 拦截 |
| 目录权限 `chown` | T24 / T25 | 否则 SQLite 写失败 |
| 翻译菜单保留占位 | T23 | 不做隐藏 |
| 不加"仅工作日" | T7 | `daily` 即每天 |

---

## 模块分工（别混）

| 模块 | 是什么 | 有店铺 | 有周期 |
|---|---|---|---|
| **工作清单** | 固定的、重复的工作 | ✅ | ✅ |
| **待办** | 临时接到的、不属于店铺的事 | ❌ | ❌ |
| 数据 | 自定义列的数据表 | ❌ | 由列语义决定 |

---

## 阶段与批次

| 批次 | 阶段 | 任务 | 上线状态 |
|---|---|---|---|
| — | A 骨架 | T1–T5 | 不可用 |
| **第一批** | B 工作清单 | T6–T12 | 可用 |
| **第一批** | C 待办 | T13–T14 | 可用 |
| **第一批** | D 数据 | T15–T18 | **第一批完成，可日常使用** |
| 第二批 | E 便签 | T19–T20 | 增强 |
| 第二批 | F 笔记 | T21–T22 | 增强 |
| 第三批 | G 翻译 | T23 | 增强 |
| — | H 部署 | T24–T27 | 正式运行 |
| — | I 验收 | T28 | 交付 |

> **建议**：第一批（T1–T18）做完就先部署上线，别等六个模块全齐。

---

# A 骨架

## T1 项目骨架

**工作量**：小

**验收标准**：
- [ ] `uvicorn app.main:app` 启动，`/api/health` 返回 `{"ok": true}`
- [ ] `npm run dev` 启动 Vite，proxy 通到后端
- [ ] `.gitignore` 含 `node_modules/`、`dist/`、`data/`、`.env`、`__pycache__/`

**涉及文件**：`backend/app/main.py`、`frontend/package.json`、`frontend/vite.config.js`

---

## T2 数据库初始化（9 张表）

**工作量**：中

**验收标准**：
- [ ] 按规格 §6 建 9 张表：`shops`、`task_templates`、`task_instances`、`todos`、`sticky_notes`、`notes`、`data_sheets`、`data_columns`、`data_rows`
- [ ] **不建 `users` 表，不建 `quick_links` 表**（快捷入口已删除）
- [ ] 删 db 文件后重启自动重建
- [ ] 种子数据：3 个店铺、6 条工作清单模板（覆盖 daily/weekly/monthly）、2 张数据表（ICBU 周数据 5 列 / 广告消耗 3 列）、2 条示例待办
- [ ] 时区 `Asia/Shanghai`

**涉及文件**：`backend/app/db.py`、`backend/scripts/seed.py`

---

## T3 单用户登录

**工作量**：中

**验收标准**：
- [ ] `POST /api/auth/login`（用户名 + bcrypt 密码）签发 HttpOnly Cookie
- [ ] `POST /api/auth/logout` 使 token 失效
- [ ] 未登录请求任意 `/api/*` 返回 401
- [ ] 失败 5 次锁 10 分钟
- [ ] `Login.vue`：`el-form` + 用户名 + 密码（`show-password`），回车提交
- [ ] 登录成功跳 `/worklist`
- [ ] 无注册、找回密码、"记住我"

**涉及文件**：`backend/app/auth.py`、`backend/app/routers/auth.py`、`frontend/src/views/Login.vue`、`frontend/src/api.js`、`frontend/src/auth.js`

---

## T4 Element Plus 接入

**工作量**：小

**验收标准**：
- [ ] `app.use(ElementPlus, { locale: zhCn })` 生效，样式完整
- [ ] 图标可用
- [ ] `npm run build` 无报错
- [ ] 未引入 pinia、axios、tailwind、富文本编辑器

**涉及文件**：`frontend/src/main.js`

---

## T5 路由与动态侧边栏

**工作量**：中

**验收标准**：
- [ ] 路由表与规格 §5.8 一致，`/` 重定向 `/worklist`
- [ ] 全局守卫：未登录 → `/login`；已登录访问 `/login` → `/worklist`
- [ ] `AdminLayout`：`el-aside` 200px 深色 `#304156` + `el-menu`（router 模式）+ `el-header` + `el-main`
- [ ] 菜单固定 6 项，顺序：工作清单 / 数据 / 待办 / 便签 / 笔记 / 翻译
- [ ] **「数据」是 `el-sub-menu`**，子项由 `GET /api/sheets` 动态渲染，末尾固定「+ 新建数据表」
- [ ] 点击「+ 新建数据表」弹 `el-dialog` 输入名称，创建后跳 `/data/:id`
- [ ] `Login` 不套 `AdminLayout`
- [ ] **菜单里没有：工作台、快捷入口、店铺管理、周报快照、系统信息**

**涉及文件**：`frontend/src/router.js`、`frontend/src/layout/AdminLayout.vue`、`frontend/src/App.vue`

---

# B 工作清单（第一批）

## T6 工作清单页骨架

**工作量**：中

**验收标准**：
- [ ] `/worklist` 页头：标题 + 「今天 10-17」+ 「管理模板」按钮
- [ ] **店铺 Tab**：`全部` + 各启用店铺 + 末尾齿轮图标（点击开店铺管理弹窗）
- [ ] **周期 Tab**：每日 / 每周 / 每月，带未完成数量角标
- [ ] 角标含义：选「全部」= 各店合计；选单店 = 该店数量
- [ ] **选「全部」时按店铺分组**（店名 + 未完成数作小标题）；选单店时平铺不分组
- [ ] **无「+ 新增今日工作」按钮**（工作清单只由模板生成）
- [ ] 切换店铺或周期重新拉数据，不整页刷新
- [ ] **空态三步引导**：`① 添加店铺 → ② 建工作清单模板 → ③ 明天自动出现`，引导内直接放按钮，店铺入口**显式可见**（不依赖齿轮）
- [ ] 1440×900 一屏，超出时卡片内部滚动

**涉及文件**：`frontend/src/views/WorkList.vue`

---

## T7 生成与顺延逻辑（后端）

**工作量**：大

**验收标准**：
- [ ] `POST /api/tasks/generate` 生成当天实例，**幂等**
- [ ] `daily` 每天生成；`weekly:N` 只在周 N 生成；`monthly:N` 只在 N 号生成
- [ ] **每月 31 号兜底**：当月无该日时在最后一天生成
- [ ] 停用店铺 / 停用模板不生成
- [ ] 未完成次日带入：**更新 `task_date` + `carried+1`**，不新建记录
- [ ] `carried` 达 7 停止带入，进逾期区
- [ ] 返回按店铺 + 周期的未完成统计

**涉及文件**：`backend/app/routers/tasks.py`

> ⚠️ 全项目最核心的逻辑。**先写测试再写实现**，必须验过这四个场景：周一生成、周二不生成、2 月兜底、顺延 7 天上限。

---

## T8 工作清单交互

**工作量**：中

**验收标准**：
- [ ] 勾选立即置灰划线，`status=done` 记 `done_at`；可取消
- [ ] **不提供「新增」入口**，页面上找不到手动加工作的按钮
- [ ] 删除需 `ElMessageBox.confirm`
- [ ] 每条：checkbox、标题、顺延标记、删除；全部视图下额外显示店铺标签
- [ ] 底部显示「今日 x/y 已完成」

**涉及文件**：`frontend/src/views/WorkList.vue`

---

## T9 逾期区与历史

**工作量**：小

**验收标准**：
- [ ] 顺延超上限的任务在「⚠ 逾期 N 项」区显示，**有逾期时常驻展开**（不折叠）
- [ ] 逾期项显示「逾期 N 天」，可「完成」或「放弃」
- [ ] 放弃后不再带入
- [ ] 无逾期时整块隐藏
- [ ] 日期选择器可查看历史某天的清单
- [ ] 历史视图按 `origin_date` 统计，显示「该日原有 X 项，其中 Y 项已顺延」

**涉及文件**：`frontend/src/views/WorkList.vue`

---

## T10 模板管理页

**工作量**：中

**验收标准**：
- [ ] `/worklist/templates` `el-table` 列：标题、店铺、周期（每日/每周一/每月5号）、排序、状态、操作
- [ ] 按店铺、按周期筛选
- [ ] 停用后不再生成，历史保留
- [ ] 上移/下移调整排序

**涉及文件**：`backend/app/routers/tasks.py`、`frontend/src/views/TemplateManage.vue`

---

## T11 模板新增/编辑弹窗

**工作量**：小

**验收标准**：
- [ ] `el-dialog` + `el-form`：标题（必填）、店铺（必选）、周期类型
- [ ] 选「每周」出现周几选择；选「每月」出现几号（1–31），并提示当月无该日取最后一天
- [ ] `repeat_rule` 存为 `daily` / `weekly:3` / `monthly:5`
- [ ] 编辑态能从 `repeat_rule` 反解出周期参数
- [ ] **保存后立即检查该模板是否匹配今天，匹配则当场补生成今日实例**，并 `ElMessage.success` 提示「已加入今日清单」
- [ ] 保存成功刷新列表

**涉及文件**：`frontend/src/views/TemplateManage.vue`

---

## T12 店铺管理弹窗

**工作量**：小

**验收标准**：
- [ ] 工作清单页店铺 Tab 末尾齿轮打开 `el-dialog`
- [ ] 弹窗内 `el-table`：店铺名、短名、排序、状态、操作
- [ ] 可新增、改名、停用、调排序
- [ ] **不提供真删除**，只能停用（避免历史数据变孤儿）
- [ ] 保存后店铺 Tab 立即刷新

**涉及文件**：`backend/app/routers/shops.py`、`frontend/src/views/components/ShopDialog.vue`

---

# C 待办（第一批）

## T13 待办列表页

**工作量**：中

**验收标准**：
- [ ] `/todos` 列表：checkbox、标题、优先级标签（高=红/低=灰）、截止日、完成、删除
- [ ] 优先级 `el-tag`：高红、普通蓝、低灰
- [ ] 截止日已过且未完成 → 日期标红
- [ ] 已完成折叠到「已完成 N 项」区域，可展开
- [ ] 顶部「+ 新增待办」弹窗：标题（必填）、备注、优先级、截止日（可空）
- [ ] 无店铺、无周期相关字段

**涉及文件**：`backend/app/routers/todos.py`、`frontend/src/views/TodoList.vue`

---

## T14 待办后端 CRUD

**工作量**：小

**验收标准**：
- [ ] `GET /api/todos`（分 todo / done 两组返回）
- [ ] `POST /api/todos`、`PATCH /api/todos/:id`（改状态/优先级等）、`DELETE /api/todos/:id`
- [ ] 完成时记 `done_at`
- [ ] 删除硬删除（临时任务不需要留痕）

**涉及文件**：`backend/app/routers/todos.py`

---

# D 数据（第一批）

## T15 数据表页（动态列渲染）

**工作量**：中

**验收标准**：
- [ ] `/data/:sheetId` 按 `data_columns` 动态渲染表头
- [ ] 按 `data_rows.values_json` 渲染单元格
- [ ] `number` 列右对齐并千分位格式化；`text` 左对齐；`date` 显示 `YYYY-MM-DD`
- [ ] **记录按 `created_at` 倒序**（最新在上）
- [ ] **底部合计行按每列的 `agg` 计算**：sum 求和 / avg 平均 / none 不显示；`text`/`date` 列留空
- [ ] 列多时表格内部横向滚动，页面不滚
- [ ] 列少时不拉伸到全宽（`min-width` 控制）
- [ ] 侧边栏对应子项高亮

**涉及文件**：`backend/app/routers/sheets.py`、`frontend/src/views/DataSheet.vue`

---

## T16 列管理弹窗

**工作量**：中

**验收标准**：
- [ ] 「管理列」打开 `el-dialog`，列出当前列：名称、类型、**合计方式**、顺序、操作
- [ ] 可新增列（名称 + 类型 + 合计方式）、改名、改类型、改合计方式、上移/下移、删除
- [ ] **合计方式**下拉：求和 / 平均 / 不合计，仅 `number` 列可选
- [ ] **同一表内列名唯一**，重名时拒绝保存并提示
- [ ] **改类型为 `number` 时校验已有值可转数字**，否则拒绝并提示
- [ ] 删除列二次确认，提示「该列数据将一并删除」
- [ ] 保存后表格立即重新渲染

**涉及文件**：`frontend/src/views/components/ColumnDialog.vue`、`backend/app/routers/sheets.py`

---

## T17 行编辑与 CSV 粘贴

**工作量**：中

**验收标准**：
- [ ] 「+ 新增记录」弹窗按列定义生成输入控件（`el-input-number` / `el-input` / `el-date-picker`）
- [ ] 行内编辑或弹窗编辑，保存后刷新
- [ ] 「粘贴 CSV」`el-input type="textarea"`，按**当前列顺序**解析
- [ ] 支持带/不带表头；字段数不符整体拒绝并报**行号**
- [ ] 粘贴成功后提示导入行数

**涉及文件**：`frontend/src/views/DataSheet.vue`、`backend/app/routers/sheets.py`

---

## T18 数据表创建与删除

**工作量**：小

**验收标准**：
- [ ] 侧边栏「+ 新建数据表」弹窗输入名称，创建后自动跳转并初始化一个默认列
- [ ] 数据表页右上角可改名、删除（二次确认，提示数据将丢失）
- [ ] 删除后侧边栏子项消失
- [ ] **删除当前正在查看的表后，跳转到第一张表；一张表都没有则显示空态**，不停留在失效路由

**涉及文件**：`backend/app/routers/sheets.py`、`frontend/src/layout/AdminLayout.vue`

---

# E 便签（第二批）

## T19 便签卡片墙

**工作量**：中

**验收标准**：
- [ ] `/sticky` 用 CSS 多列布局（`column-count`）排卡片
- [ ] 卡片显示内容（多行溢出省略）、颜色、置顶标记
- [ ] 点击卡片内联编辑（`textarea`），失焦保存
- [ ] 可改颜色（五色）、置顶、删除
- [ ] 「+ 新建便签」创建空白卡片并聚焦
- [ ] **删除策略**：原本有内容后被清空才删除；新建后从未输入的空卡片**保留**，不自动删

**涉及文件**：`frontend/src/views/StickyBoard.vue`

---

## T20 便签后端

**工作量**：小

**验收标准**：
- [ ] `GET/POST/PATCH/DELETE /api/sticky`
- [ ] 置顶项排在前面
- [ ] 内容为空时保存即删除（避免留空卡片）

**涉及文件**：`backend/app/routers/sticky.py`

---

# F 笔记（第二批）

## T21 笔记列表与详情

**工作量**：中

**验收标准**：
- [ ] `/notes` 左侧列表（标题 + 更新时间），右侧编辑区
- [ ] 标题输入 + 正文 `el-input type="textarea"`（纯文本，不引富文本编辑器）
- [ ] 自动保存（失焦或 2 秒防抖）
- [ ] 列表顶部搜索框，按标题过滤
- [ ] **列表项右侧有删除按钮**，二次确认后删除并跳转列表

**涉及文件**：`frontend/src/views/NoteList.vue`、`frontend/src/views/NoteDetail.vue`

---

## T22 笔记后端

**工作量**：小

**验收标准**：
- [ ] `GET/POST/PATCH/DELETE /api/notes`
- [ ] 按 `updated_at` 倒序
- [ ] 支持标题模糊搜索

**涉及文件**：`backend/app/routers/notes.py`

---

# G 翻译（第三批）

## T23 翻译界面占位

**工作量**：小

**验收标准**：
- [ ] `/translate` 左右两个输入区 + 中间交换按钮
- [ ] 语言固定「中文 ↔ 英文」，可点击交换
- [ ] 「翻译」按钮点击后提示「翻译接口待接入」，**不发起任何请求**
- [ ] 页面明确标注「功能开发中」，不假装能用

**涉及文件**：`frontend/src/views/Translate.vue`

---

# H 部署

## T24 Docker 多阶段构建

**工作量**：中

**验收标准**：
- [ ] `node:22` 构建前端 → 产物进 `python:3.13-slim`
- [ ] `docker compose up -d` 后看到登录页
- [ ] **刷新 `/worklist` 不 404**（非 `/api` 路径回退 index.html）
- [ ] `data/`、`backups/` 挂载卷
- [ ] 环境变量从 `.env` 读取，时区 `Asia/Shanghai`
- [ ] `.dockerignore` 排除 `node_modules/`、`data/`、`.git`
- [ ] 提供 `scripts/make-password.py`，运行后输出 bcrypt 哈希，可直接贴进 `.env` 的 `WB_PASSWORD_HASH`
- [ ] 部署说明写明宿主机需执行 `chown -R 1000:1000 data backups`，否则容器内 SQLite 写入失败
- [ ] `.env.example` 含全部变量与注释说明

---

## T25 服务器部署

**工作量**：中

**验收标准**：
- [ ] 代码在 `/opt/workbench/`
- [ ] 容器监听 `127.0.0.1:8000`
- [ ] `restart: unless-stopped`
- [ ] 重启服务器自恢复

---

## T26 Nginx 与 HTTPS

**工作量**：中

**验收标准**：
- [ ] 域名可访问，登录与路由跳转正常
- [ ] HTTP 跳 HTTPS，证书自动续期已配置
- [ ] 公网仅开 80/443，8000 外网不可达
- [ ] SPA 刷新不 404

---

## T27 每日备份

**工作量**：小

**验收标准**：
- [ ] cron `0 3 * * *` 生成 `backups/wb-YYYY-MM-DD.db`
- [ ] 保留 14 份
- [ ] **实际验证一次备份可打开**
- [ ] 提供 `scripts/restore.sh`：停容器 → 用指定备份覆盖 `data/workbench.db` → 起容器
- [ ] 部署说明写出恢复步骤（不依赖脚本也能手动操作）

---

# I 验收

## T28 全量验收

**验收标准**：
- [ ] 安全：未登录无法访问任何接口；公网 8000 不可达
- [ ] 单用户：无 `users` 表、无注册入口
- [ ] **侧边栏严格 6 项，顺序正确，无「工作台」「快捷入口」「周报」「系统信息」**
- [ ] **「数据」子菜单由数据库动态渲染，新建/删除后立即更新**
- [ ] 工作清单：三周期生成正确、31 号兜底、顺延是更新而非新建、7 天上限生效
- [ ] **工作清单页找不到任何"手动新增"入口**
- [ ] **「全部店铺」视图按店分组，单店视图平铺**
- [ ] **新建模板后当天清单立即出现该项**
- [ ] **首次使用的空态有三步引导，且店铺入口可见**
- [ ] **逾期区有内容时自动展开**
- [ ] 待办：无店铺字段、完成后折叠、优先级与截止日显示正确
- [ ] 数据：动态列渲染、**合计按列各自 agg 计算**、列名不可重复、改列类型有校验、CSV 报行号
- [ ] **删除正在查看的数据表后跳到第一张表，不白屏**
- [ ] 便签：卡片墙布局正常、置顶生效、**新建空卡片不会被自动删除**
- [ ] 笔记：自动保存、搜索可用、**可删除**
- [ ] 翻译：按钮不发起请求，有「待接入」提示
- [ ] **Session 失效时页面自动跳登录页，不白屏**
- [ ] 布局：**1440×900 一屏不滚**
- [ ] 部署：重启自恢复；`make-password.py` 可用
- [ ] 备份：**按 `restore.sh` 实际恢复成功一次**
- [ ] 范围：无 §4「明确不做」中的功能

---

## 质量底线

- [ ] 不引入 pinia、axios、tailwind、图表库、富文本编辑器
- [ ] 能用 Element 现成组件就不自己写 CSS，不自定义主题
- [ ] 不做动画与视觉打磨
- [ ] 接口统一 `{ok, data, error}`
- [ ] 前端 API 统一走 `api.js`
- [ ] 字段名与 §6 一致
- [ ] 生成类接口必须幂等
- [ ] 新增规格外功能前先回到 §4 确认

---

## 常见坑

| 坑 | 后果 | 规避 |
|---|---|---|
| 用 UTC 算"今天" | 早上看到昨天的清单 | 固定 `Asia/Shanghai` |
| 生成接口不幂等 | 刷新一次多一份 | 生成前查当天该模板是否已存在 |
| **每月 31 号没兜底** | 2 月任务永不出现 | 当月无该日取最后一天 |
| 顺延新建记录 | 一条变三条 | 更新 `task_date` + `carried+1` |
| **数据列用固定字段存** | 加列要改表结构，等于白做 | 必须用 `values_json` 存 |
| 改列类型不校验 | 文本混入数字列，合计变 NaN | 转 `number` 前校验全部可转 |
| 删列不提示 | 数据静默丢失 | 二次确认 + 明确写"数据将删除" |
| 店铺真删除 | 历史待办变孤儿 | 只停用不真删 |
| 侧边栏菜单写死 | 新建数据表不出现 | 必须从接口动态渲染 |
| SQLite 没挂卷 | 容器重启数据全丢 | `data/` 必须 volume |
| SPA 刷新 404 | 直接访问 `/worklist` 报错 | 非 `/api` 回退 index.html |
| 笔记引富文本编辑器 | 包大一倍，还得处理粘贴 HTML | 纯文本 textarea 够用 |
| **新建模板不补生成** | 当天看不到，以为坏了 | 保存后检查当天是否匹配并补生成 |
| **顺延只改 task_date** | 查历史看不到当天欠了几项 | 加 `origin_date` 分开记 |
| **数字列一律求和** | 转化率、客单价被加总，数字是错的 | 列级 `agg`：sum/avg/none |
| **按 1920 设计布局** | 14 寸笔记本上挤压或横向滚动 | 验收基准 1440×900 |
| **401 没统一处理** | Session 过期后白屏报错 | `api.js` 拦截 401 → 跳登录 |
| **容器 UID 与宿主机不一致** | SQLite 写入失败，页面报错 | 部署时 `chown -R 1000:1000 data` |

---

## 交付物

1. `ai/memory-bank/site-setup.md` — 规格 v3.1（已完成）
2. 本任务清单（已完成）
3. `ai/memory-bank/review-walkthrough-v3.0.md` — 走查报告（已完成）
4. 可运行代码（T1–T23）
5. 部署文件：`Dockerfile`、`docker-compose.yml`、`.dockerignore`、`.env.example`、Nginx 配置
6. 脚本：`scripts/seed.py`、`scripts/make-password.py`、`scripts/backup.sh`、`scripts/restore.sh`
7. 部署说明（含密码生成、权限设置、备份恢复三步）
