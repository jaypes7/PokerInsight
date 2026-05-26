from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import monotonic
from uuid import uuid4

import redis.asyncio as redis
import structlog
from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.core.config import Settings, get_settings
from app.db.session import engine, get_db
from app.observability.logging import configure_logging

log = structlog.get_logger()
DB_DEPENDENCY = Depends(get_db)
SETTINGS_DEPENDENCY = Depends(get_settings)


class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    version: str
    sha: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    app.state.settings = settings
    app.state.redis = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    log.info("api_started")
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await engine.dispose()
        log.info("api_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    if settings.is_production:
        docs_url = None
        redoc_url = None

    app = FastAPI(
        title="PokerInsight API",
        version=settings.app_version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)
        started_at = monotonic()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        except Exception:
            log.exception("request_failed")
            raise
        finally:
            latency_ms = int((monotonic() - started_at) * 1000)
            status_code = response.status_code if response is not None else 500
            log.info("request", status=status_code, latency_ms=latency_ms)
            clear_contextvars()
            if response is not None:
                response.headers["X-Request-ID"] = request_id

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/readyz", response_model=HealthResponse)
    async def readyz(db: AsyncSession = DB_DEPENDENCY) -> HealthResponse | JSONResponse:
        try:
            await db.execute(text("SELECT 1"))
            await app.state.redis.ping()
        except Exception:
            log.exception("readiness_failed")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unavailable"},
            )
        return HealthResponse(status="ok")

    @app.get("/version", response_model=VersionResponse)
    async def version(settings: Settings = SETTINGS_DEPENDENCY) -> VersionResponse:
        return VersionResponse(version=settings.app_version, sha=settings.git_sha)

    return app


app = create_app()
