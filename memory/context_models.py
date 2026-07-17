"""Context models for memory layer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryContext(BaseModel):
    """Context model for memory-related operations."""

    recent_workflows: list[dict[str, Any]] = Field(default_factory=list)
    agent_history: list[dict[str, Any]] = Field(default_factory=list)
    memory_summary: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")
