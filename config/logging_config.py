"""Centralized Loguru logging configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO") -> None:
    """Configure console and rotating file logging for the application."""
    project_root = Path(__file__).resolve().parents[1]
    log_directory = project_root / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        log_directory / "app.log",
        level=log_level,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    )
