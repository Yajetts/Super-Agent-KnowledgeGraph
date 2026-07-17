"""SQLAlchemy ORM models for skills persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory.models import Base


class Skill(Base):
    """ORM model for storing skill definitions in PostgreSQL."""

    __tablename__ = "skills"

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    agent_skills: Mapped[list["AgentSkill"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    metrics: Mapped[list["SkillMetrics"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class AgentSkill(Base):
    """ORM model for storing agent-skill assignments in PostgreSQL."""

    __tablename__ = "agent_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(200), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    skill: Mapped["Skill"] = relationship(back_populates="agent_skills")


class SkillMetrics(Base):
    """ORM model for storing skill usage metrics."""

    __tablename__ = "skill_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"), nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invocation_frequency: Mapped[float] = mapped_column(Integer, default=0.0, nullable=False)
    avg_performance_with_skill: Mapped[float] = mapped_column(Integer, default=0.0, nullable=False)
    avg_performance_without_skill: Mapped[float] = mapped_column(Integer, default=0.0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    skill: Mapped["Skill"] = relationship(back_populates="metrics")
