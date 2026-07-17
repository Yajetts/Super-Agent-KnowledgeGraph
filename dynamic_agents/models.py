"""Data models for dynamic agent creation and management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from memory.models import Base


class AgentProfile(BaseModel):
    """Metadata model for a dynamic agent profile."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name of the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    skills: list[str] = Field(default_factory=list, description="List of skills the agent possesses")
    supported_task_types: list[str] = Field(
        default_factory=list, description="Task types this agent can handle"
    )
    creation_source: str = Field(
        default="dynamic", description="Source of agent creation (static/dynamic)"
    )
    usage_count: int = Field(default=0, ge=0, description="Number of times this agent has been used")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the agent was created")
    last_used: datetime | None = Field(default=None, description="When the agent was last used")
    success_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Average success score of agent executions")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score based on task matching")
    is_dynamic: bool = Field(default=True, description="Whether this is a dynamically created agent")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DynamicAgentRecord(Base):
    """SQLAlchemy ORM model for storing dynamic agent definitions in PostgreSQL."""

    __tablename__ = "dynamic_agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of skills
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_used: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success_score: Mapped[float] = mapped_column(Integer, default=1.0, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Integer, default=1.0, nullable=False)


class CapabilityGap(BaseModel):
    """Model representing a detected capability gap."""

    required_skill: str = Field(..., description="Skill that is missing")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence that this skill is needed")
    context: str = Field(default="", description="Context for why this skill is needed")


class TaskAnalysis(BaseModel):
    """Model representing the analysis of a task's requirements."""

    task_query: str = Field(..., description="The original task query")
    task_type: str = Field(..., description="Inferred task type")
    required_skills: list[str] = Field(default_factory=list, description="Skills required for the task")
    capability_gaps: list[CapabilityGap] = Field(
        default_factory=list, description="Detected capability gaps"
    )
    coverage_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How well existing agents cover the required skills",
    )
    should_create_agent: bool = Field(
        default=False,
        description="Whether a new agent should be created based on coverage",
    )


class AgentGenerationRequest(BaseModel):
    """Model for requesting agent generation."""

    task_query: str = Field(..., description="The task that requires the new agent")
    required_skills: list[str] = Field(..., description="Skills the agent must have")
    task_type: str = Field(..., description="Type of task the agent will handle")
    context: str = Field(default="", description="Additional context for agent generation")


class AgentGenerationResponse(BaseModel):
    """Model for agent generation response."""

    agent_profile: AgentProfile = Field(..., description="The generated agent profile")
    system_prompt: str = Field(..., description="The generated system prompt")
    success: bool = Field(..., description="Whether generation was successful")
    error: str = Field(default="", description="Error message if generation failed")
