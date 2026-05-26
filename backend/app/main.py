"""FastAPI application entry point."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health, videos

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Abet Videos API",
    description="AI-powered video generation backend",
    version="0.1.0",
)

# CORS middleware - allow all origins for development
# Note: allow_credentials=True is invalid with wildcard origins per the Fetch spec,
# so credentials are disabled when using allow_origins=["*"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(videos.router)


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    output_path = Path(settings.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Mount static files for serving generated videos
    videos_dir = output_path / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/videos", StaticFiles(directory=str(videos_dir)), name="videos")

    # Serve frontend build at root if it exists (production single-container mode)
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists() and frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    logging.getLogger(__name__).info(
        f"Server started. Output directory: {output_path.resolve()}"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logging.getLogger(__name__).info("Server shutting down")
