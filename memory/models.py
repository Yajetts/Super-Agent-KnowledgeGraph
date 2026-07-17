"""SQLAlchemy ORM models for memory persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class WorkflowMemory(Base):
    """Store workflow execution metadata and results."""

    __tablename__ = "workflow_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)
    agents_used: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of agent names
    graph_results_count: Mapped[int] = mapped_column(Integer, default=0)
    vector_results_count: Mapped[int] = mapped_column(Integer, default=0)
    fusion_results_count: Mapped[int] = mapped_column(Integer, default=0)

    agent_executions: Mapped[list["AgentExecutionMemory"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan"
    )
    retrieval_memory: Mapped["RetrievalMemory"] = relationship(
        back_populates="workflow", uselist=False, cascade="all, delete-orphan"
    )


class AgentExecutionMemory(Base):
    """Store individual agent execution details."""

    __tablename__ = "agent_execution_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_memory.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    execution_order: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)

    workflow: Mapped["WorkflowMemory"] = relationship(back_populates="agent_executions")


class RetrievalMemory(Base):
    """Store retrieval metadata for each workflow."""

    __tablename__ = "retrieval_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_memory.id"), nullable=False, unique=True)
    graph_results: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    vector_results: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    fusion_results: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string

    workflow: Mapped["WorkflowMemory"] = relationship(back_populates="retrieval_memory")
