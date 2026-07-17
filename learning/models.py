"""Data models for workflow learning and reflection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowReflection(BaseModel):
    """Model for storing workflow execution reflections."""

    workflow_id: int = Field(..., description="ID of the workflow in memory")
    task_type: str = Field(..., description="Type of task executed")
    workflow_pattern: str = Field(..., description="String representation of agent sequence")
    agents_used: list[str] = Field(..., description="List of agent names in execution order")
    execution_time: float = Field(..., description="Total execution time in seconds")
    retrieval_count: int = Field(..., description="Total number of retrieval operations")
    reflection_summary: str = Field(..., description="Generated reflection summary")
    success_score: float = Field(..., ge=0.0, le=1.0, description="Success score between 0.0 and 1.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the reflection was created")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowRecommendation(BaseModel):
    """Model for workflow recommendations based on learned patterns."""

    task_type: str = Field(..., description="Type of task for recommendation")
    recommended_agents: list[str] = Field(..., description="Recommended agent sequence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for recommendation")
    supporting_examples: int = Field(..., ge=0, description="Number of historical examples supporting this")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowPattern(BaseModel):
    """Model for storing learned workflow patterns."""

    id: int | None = Field(None, description="Database ID")
    task_type: str = Field(..., description="Type of task this pattern applies to")
    workflow_pattern: list[str] = Field(..., description="Agent sequence as a list")
    success_score: float = Field(..., ge=0.0, le=1.0, description="Average success score")
    usage_count: int = Field(default=1, ge=1, description="Number of times this pattern was used")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class LearningStats(BaseModel):
    """Model for learning system statistics."""

    reflections: int = Field(..., ge=0, description="Total number of reflections stored")
    patterns: int = Field(..., ge=0, description="Total number of patterns discovered")
    successful_patterns: int = Field(..., ge=0, description="Number of patterns with success score > 0.7")
    avg_success_score: float = Field(..., ge=0.0, le=1.0, description="Average success score across all patterns")
