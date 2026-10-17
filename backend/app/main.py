from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, db
from .errors import register_exception_handlers
from .routers import auth as auth_router
from .routers import notes as notes_router
from .routers import sheets as sheets_router
from .routers import shops as shops_router
from .routers import sticky as sticky_router
from .routers import tasks as tasks_router
from .routers import todos as todos_router

DIST_DIR = config.PROJECT_DIR / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    config.validate()  # 配置不全直接启动失败，不带着坏配置跑
    db.init_db()
    print(f"[boot] db={config.DB_PATH} tz={config.TIMEZONE}")
    yield


app = FastAPI(title="个人工作台", version="0.1.0", lifespan=lifespan)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(shops_router.router)
app.include_router(tasks_router.router)
app.include_router(tasks_router.router_tpl)
app.include_router(sheets_router.router)
app.include_router(todos_router.router)
app.include_router(sticky_router.router)
app.include_router(notes_router.router)


@app.get("/api/health")
def health():
    return {"ok": True, "data": {"status": "up"}, "error": None}


# ---------- 前端静态资源 ----------
# 开发阶段由 Vite(5173) 提供页面，这里只在构建产物存在时接管；
# SPA 需要把所有非 /api 路径回退到 index.html，否则刷新 /worklist 会 404。

if DIST_DIR.is_dir():
    assets = DIST_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"ok": False, "data": None, "error": {"code": "not_found", "message": "接口不存在"}}, 404)
        candidate: Path = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
else:

    @app.get("/", include_in_schema=False)
    def dev_hint():
        return JSONResponse(
            {
                "ok": True,
                "data": {
                    "message": "前端尚未构建。开发请访问 Vite 服务（默认 http://localhost:5173）",
                },
                "error": None,
            }
        )
