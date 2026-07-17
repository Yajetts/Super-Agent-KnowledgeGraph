"""Database connection and session management for memory layer."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings
from memory.models import Base


class DatabaseManager:
    """Manage PostgreSQL database connections and table creation."""

    def __init__(self) -> None:
        """Initialize database manager with settings."""
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None

    def connect(self) -> None:
        """Create database engine and session factory."""
        try:
            database_url = (
                f"postgresql://{self.settings.postgres_user}:{self.settings.postgres_password}"
                f"@{self.settings.postgres_host}:{self.settings.postgres_port}/{self.settings.postgres_db}"
            )
            self.engine = create_engine(database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection established successfully")
        except ImportError as exc:
            logger.error("PostgreSQL driver not installed: {}. Memory layer will be disabled.", exc)
            self.engine = None
            self.SessionLocal = None
        except Exception as exc:
            logger.error("Database connection failed: {}. Memory layer will be disabled.", exc)
            self.engine = None
            self.SessionLocal = None

    def create_tables(self) -> None:
        """Create all tables in the database."""
        try:
            if self.engine is None:
                self.connect()
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as exc:
            logger.error("Failed to create database tables: {}", exc)
            raise

    def get_session(self) -> Session:
        """Get a new database session."""
        if self.SessionLocal is None:
            self.connect()
        if self.SessionLocal is None:
            raise RuntimeError("Database connection unavailable")
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Database session error, transaction rolled back: {}", exc)
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connections."""
        if self.engine is not None:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get or create the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
