import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import api_router
from backend.config import settings
from backend.config.settings import BASE_DIR
from backend.utils.rate_limit import RateLimitMiddleware
from backend.utils.security import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


def create_app() -> FastAPI:
    docs_url = None if settings.use_webhook else "/docs"
    redoc_url = None if settings.use_webhook else "/redoc"
    app = FastAPI(title="Еда Рядом API", version="1.0.0", docs_url=docs_url, redoc_url=redoc_url)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.include_router(api_router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/tonconnect-manifest.json", include_in_schema=False)
    async def tonconnect_manifest() -> dict:
        base = settings.public_url or "https://food-mafia-bot.onrender.com"
        return {
            "url": base,
            "name": "Еда Рядом",
            "iconUrl": f"{base}/favicon.ico",
        }

    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    if FRONTEND_DIST.exists():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa(full_path: str) -> FileResponse:
            candidate = (FRONTEND_DIST / full_path).resolve()
            if (
                full_path
                and candidate.is_file()
                and Path(FRONTEND_DIST).resolve() in candidate.parents
            ):
                return FileResponse(candidate)
            return FileResponse(FRONTEND_DIST / "index.html")
    else:
        logger.warning("frontend/dist not found — Mini App static files are not served")

    return app
