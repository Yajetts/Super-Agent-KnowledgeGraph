"""Application startup wiring."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api import routes
from config.logging_config import setup_logging
from config.settings import Settings
from memory.database import get_db_manager


def configure_application(app: FastAPI, settings: Settings) -> None:
    """Attach shared application state and initialize logging."""
    setup_logging(log_level=settings.log_level)
    app.state.settings = settings
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register controller cleanup on shutdown
    @app.on_event("shutdown")
    async def cleanup_controller():
        from api.routes import get_controller, get_graph_manager
        try:
            controller = get_controller()
            if controller:
                controller.close()
        except Exception:
            pass
        try:
            graph_manager = get_graph_manager()
            if graph_manager:
                graph_manager.close()
        except Exception:
            pass
    
    # Initialize memory database tables
    try:
        db_manager = get_db_manager()
        db_manager.connect()
        db_manager.create_tables()
        logger.info("Memory database initialized successfully")
    except Exception as exc:
        logger.warning("Memory database initialization failed: {}. System will continue without memory persistence.", exc)
