"""FastAPI application entry point."""

import logging
import os
import uuid
from contextvars import ContextVar
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health, settings as settings_router, videos, auth
from app.settings_manager import load_runtime_settings

_LOG_FORMAT = os.getenv("LOG_FORMAT", "dev")
if _LOG_FORMAT == "json":
    from pythonjsonlogger import jsonlogger
    _handler = logging.StreamHandler()
    _handler.setFormatter(jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
    ))
    logging.basicConfig(level=logging.INFO, handlers=[_handler])
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
shared_http_client: httpx.AsyncClient | None = None
MAX_BODY_SIZE = 10 * 1024 * 1024

app = FastAPI(
    title="Abet Videos API",
    description="AI-powered video generation backend",
    version="0.1.0",
)

origins = (
    ["*"]
    if settings.cors_origins == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    request_id_ctx.set(rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(status_code=413, detail="Request body too large")
    return await call_next(request)


def get_request_id() -> str:
    return request_id_ctx.get()


def get_http_client() -> httpx.AsyncClient:
    global shared_http_client
    if shared_http_client is None or shared_http_client.is_closed:
        shared_http_client = httpx.AsyncClient(timeout=30.0)
    return shared_http_client


# Sentry initialization
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        enable_tracing=True,
        traces_sample_rate=0.1,
    )
    logging.getLogger(__name__).info("Sentry initialized")

app.include_router(health.router)
app.include_router(settings_router.router)
app.include_router(videos.router)
app.include_router(auth.router)


@app.on_event("startup")
async def startup_event():
    output_path = Path(settings.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    load_runtime_settings()

    videos_dir = output_path / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/videos", StaticFiles(directory=str(videos_dir)), name="videos")

    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists() and frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    logging.getLogger(__name__).info(
        f"Server started. Output directory: {output_path.resolve()}"
    )


@app.on_event("shutdown")
async def shutdown_event():
    global shared_http_client
    if shared_http_client is not None:
        await shared_http_client.aclose()
        shared_http_client = None
    logging.getLogger(__name__).info("Server shutting down")
