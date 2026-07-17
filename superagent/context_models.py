"""Structured context models shared across the SuperAgent workflow."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Finding(BaseModel):
    """Structured research observation produced by an agent."""

    source_agent: str
    category: str
    content: str
    confidence: float

    model_config = ConfigDict(extra="forbid")

    @field_validator("confidence")
    @classmethod
    def _validate_confidence(cls, value: float) -> float:
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value


class Recommendation(BaseModel):
    """Structured strategy recommendation produced by an agent."""

    source_agent: str
    content: str
    priority: str

    model_config = ConfigDict(extra="forbid")


class Risk(BaseModel):
    """Structured risk signal produced by an agent."""

    source_agent: str
    description: str
    severity: str

    model_config = ConfigDict(extra="forbid")


class GraphContext(BaseModel):
    """Historical context retrieved from the knowledge graph."""

    related_tasks: list[dict[str, object]] = Field(default_factory=list)
    related_findings: list[dict[str, object]] = Field(default_factory=list)
    related_risks: list[dict[str, object]] = Field(default_factory=list)
    related_recommendations: list[dict[str, object]] = Field(default_factory=list)
    summary: str = ""

    model_config = ConfigDict(extra="forbid")


class TaskContext(BaseModel):
    """Mutable state shared across sequential agent execution."""

    query: str
    task_type: str
    findings: list[Finding] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    agent_history: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    graph_context: GraphContext | None = None
    graphrag_context: GraphRAGContext | None = None

    model_config = ConfigDict(extra="forbid")


class GraphRAGContext(BaseModel):
    """Unified context combining graph retrieval and vector retrieval."""

    query: str
    graph_results: list[dict[str, object]] = Field(default_factory=list)
    vector_results: list[dict[str, object]] = Field(default_factory=list)
    merged_findings: list[dict[str, object]] = Field(default_factory=list)
    merged_risks: list[dict[str, object]] = Field(default_factory=list)
    merged_recommendations: list[dict[str, object]] = Field(default_factory=list)
    context_summary: str = ""
    retrieval_metadata: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class WorkflowResult(BaseModel):
    """Structured output returned after sequential agent execution."""

    query: str
    task_type: str
    agents_used: list[str]
    findings: list[Finding]
    risks: list[Risk]
    recommendations: list[Recommendation]
    execution_time: float = 0.0
    workflow_id: int | None = None
    chain_of_thought: str = ""
    formatted_response: str = ""

    model_config = ConfigDict(extra="forbid")