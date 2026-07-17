"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes import router as api_router
from app.startup import configure_application
from config.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    app = FastAPI(
        title="SuperAgent Knowledge Graph",
        description="AI-driven Decision Intelligence Platform foundation.",
        version="0.1.0",
    )
    configure_application(app=app, settings=settings)
    app.include_router(api_router)
    return app


app = create_app()
