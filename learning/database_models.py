"""SQLAlchemy ORM models for learning layer persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from memory.models import Base


class WorkflowReflectionDB(Base):
    """Store workflow execution reflections in the database."""

    __tablename__ = "workflow_reflections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(Integer, nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    workflow_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    agents_used: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of agent names
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)
    retrieval_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reflection_summary: Mapped[str] = mapped_column(Text, nullable=False)
    success_score: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class WorkflowPatternDB(Base):
    """Store learned workflow patterns in the database."""

    __tablename__ = "workflow_patterns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    workflow_pattern: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of agent sequence
    success_score: Mapped[float] = mapped_column(Float, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
