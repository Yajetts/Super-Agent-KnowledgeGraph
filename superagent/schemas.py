"""Pydantic models for SuperAgent task analysis and execution planning."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from superagent.context_models import Finding, Recommendation, Risk, WorkflowResult


class TaskAnalysis(BaseModel):
    """Structured result produced by the task analyzer."""

    task_type: str
    complexity: str
    subtasks: list[str]
    required_skills: list[str]

    model_config = ConfigDict(extra="forbid")


class ExecutionPlan(BaseModel):
    """Structured plan returned by the SuperAgent controller."""

    query: str
    task_type: str
    selected_agents: list[str]
    subtasks: list[str]
    required_skills: list[str]
    execution_order: list[str]

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "Finding",
    "Recommendation",
    "Risk",
    "TaskAnalysis",
    "ExecutionPlan",
    "WorkflowResult",
]