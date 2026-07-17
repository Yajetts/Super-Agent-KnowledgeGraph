"""Pydantic schemas for HTTP responses and requests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agents.agent_metadata import AgentMetadata

from superagent.schemas import WorkflowResult


class RootResponse(BaseModel):
    """Response schema for the API root endpoint."""

    status: Literal["running"]
    project: Literal["SuperAgent Knowledge Graph"]

    model_config = ConfigDict(extra="forbid")


class ExecuteRequest(BaseModel):
    """Request schema for workflow execution."""

    query: str

    model_config = ConfigDict(extra="forbid")


class ExecuteResponse(WorkflowResult):
    """Response schema for workflow execution."""

    execution_time: float = 0.0
    workflow_id: int | None = None
    chain_of_thought: str = ""

    model_config = ConfigDict(extra="forbid")


class GraphStatsResponse(BaseModel):
    """Statistics for the persisted knowledge graph."""

    tasks: int
    agents: int
    findings: int
    risks: int
    recommendations: int

    model_config = ConfigDict(extra="forbid")


class GraphSchemaNodeType(BaseModel):
    """Describe a node type available in the graph schema."""

    label: str
    properties: list[str]

    model_config = ConfigDict(extra="forbid")


class GraphSchemaRelationshipType(BaseModel):
    """Describe a relationship type available in the graph schema."""

    type: str
    source: str
    target: str

    model_config = ConfigDict(extra="forbid")


class GraphSchemaResponse(BaseModel):
    """Summary of the graph structure and agent metadata."""

    node_types: list[GraphSchemaNodeType]
    relationship_types: list[GraphSchemaRelationshipType]
    agents: list[AgentMetadata] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class GraphContextResponse(BaseModel):
    """Retrieved historical context for a supplied query."""

    related_tasks: list[dict[str, object]] = Field(default_factory=list)
    related_findings: list[dict[str, object]] = Field(default_factory=list)
    related_risks: list[dict[str, object]] = Field(default_factory=list)
    related_recommendations: list[dict[str, object]] = Field(default_factory=list)
    summary: str

    model_config = ConfigDict(extra="forbid")


AnalyzeRequest = ExecuteRequest
AnalyzeResponse = ExecuteResponse


class VectorStatsResponse(BaseModel):
    """Statistics for the vector database."""

    documents: int

    model_config = ConfigDict(extra="forbid")


class VectorSearchResult(BaseModel):
    """Single result from a vector search."""

    document_id: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)
    similarity_score: float

    model_config = ConfigDict(extra="forbid")


class VectorSearchResponse(BaseModel):
    """Response from a vector search query."""

    results: list[VectorSearchResult] = Field(default_factory=list)
    summary: str = ""
    query: str

    model_config = ConfigDict(extra="forbid")


class GraphRAGStatsResponse(BaseModel):
    """Statistics for the GraphRAG system."""

    graph_nodes: int = 0
    vector_documents: int = 0
    fusion_results: int = 0
    graph_available: bool = False
    vector_available: bool = False

    model_config = ConfigDict(extra="forbid")


class GraphRAGContextResponse(BaseModel):
    """Retrieved GraphRAG context for a supplied query."""

    query: str
    graph_results: list[dict[str, object]] = Field(default_factory=list)
    vector_results: list[dict[str, object]] = Field(default_factory=list)
    merged_findings: list[dict[str, object]] = Field(default_factory=list)
    merged_risks: list[dict[str, object]] = Field(default_factory=list)
    merged_recommendations: list[dict[str, object]] = Field(default_factory=list)
    context_summary: str = ""
    retrieval_metadata: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class MemoryStatsResponse(BaseModel):
    """Statistics for the memory repository."""

    workflows: int
    agent_executions: int
    retrieval_records: int

    model_config = ConfigDict(extra="forbid")


class WorkflowMemoryItem(BaseModel):
    """Single workflow memory item."""

    id: int
    query: str
    task_type: str
    timestamp: str
    execution_time: float
    agents_used: list[str]
    graph_results_count: int
    vector_results_count: int
    fusion_results_count: int

    model_config = ConfigDict(extra="forbid")


class MemoryRecentResponse(BaseModel):
    """Recent workflow history."""

    workflows: list[WorkflowMemoryItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class AgentUsageItem(BaseModel):
    """Agent usage statistics item."""

    agent_name: str
    usage_count: int

    model_config = ConfigDict(extra="forbid")


class AgentUsageStatsItem(BaseModel):
    """Detailed agent usage statistics item."""

    agent_name: str
    total_executions: int
    average_execution_time: float
    min_execution_time: float
    max_execution_time: float

    model_config = ConfigDict(extra="forbid")


class MemoryAgentsResponse(BaseModel):
    """Agent usage statistics."""

    most_used_agents: list[AgentUsageItem] = Field(default_factory=list)
    agent_usage_statistics: list[AgentUsageStatsItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class LearningPatternItem(BaseModel):
    """Single learned workflow pattern item."""

    task_type: str
    workflow_pattern: list[str]
    success_score: float
    usage_count: int
    last_updated: str

    model_config = ConfigDict(extra="forbid")


class LearningPatternsResponse(BaseModel):
    """Learned workflow patterns."""

    patterns: list[LearningPatternItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class LearningRecommendationResponse(BaseModel):
    """Workflow recommendation for a task type."""

    task_type: str
    recommended_agents: list[str]
    confidence: float
    supporting_examples: int

    model_config = ConfigDict(extra="forbid")


class LearningStatsResponse(BaseModel):
    """Learning system statistics."""

    reflections: int
    patterns: int
    successful_patterns: int
    avg_success_score: float

    model_config = ConfigDict(extra="forbid")


class AgentItem(BaseModel):
    """Single agent item."""

    name: str
    description: str
    skills: list[str]
    task_types: list[str] = Field(default_factory=list)
    creation_source: str
    creation_timestamp: str | None = None
    usage_count: int
    is_dynamic: bool
    last_used: str | None = None
    success_score: float | None = None
    relevance_score: float | None = None

    model_config = ConfigDict(extra="forbid")


class AgentsResponse(BaseModel):
    """Response for all agents."""

    agents: list[AgentItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class DynamicAgentsResponse(BaseModel):
    """Response for dynamic agents only."""

    agents: list[AgentItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class AgentDetailResponse(BaseModel):
    """Detailed response for a single agent."""

    name: str
    description: str
    skills: list[str]
    task_types: list[str] = Field(default_factory=list)
    creation_source: str
    creation_timestamp: str | None = None
    usage_count: int
    is_dynamic: bool
    system_prompt: str = ""

    model_config = ConfigDict(extra="forbid")


class CreateAgentRequest(BaseModel):
    """Request for creating a dynamic agent."""

    name: str
    description: str
    skills: list[str]
    task_type: str
    system_prompt: str = ""

    model_config = ConfigDict(extra="forbid")


class CreateAgentResponse(BaseModel):
    """Response for creating a dynamic agent."""

    success: bool
    agent_name: str
    message: str

    model_config = ConfigDict(extra="forbid")


class TaskAnalysisResponse(BaseModel):
    """Response for task capability analysis."""

    task_query: str
    task_type: str
    required_skills: list[str]
    capability_gaps: list[dict[str, object]] = Field(default_factory=list)
    coverage_score: float
    should_create_agent: bool

    model_config = ConfigDict(extra="forbid")


class SkillItem(BaseModel):
    """Single skill item."""

    skill_id: int
    skill_name: str
    description: str
    file_path: str
    created_at: str

    model_config = ConfigDict(extra="forbid")


class SkillsResponse(BaseModel):
    """Response for all skills."""

    skills: list[SkillItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SkillMetricsItem(BaseModel):
    """Skill metrics item."""

    skill_id: int
    skill_name: str
    usage_count: int
    invocation_frequency: float
    avg_performance_with_skill: float
    avg_performance_without_skill: float
    last_updated: str

    model_config = ConfigDict(extra="forbid")


class SkillMetricsResponse(BaseModel):
    """Response for skill metrics."""

    metrics: list[SkillMetricsItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SkillStatsResponse(BaseModel):
    """Response for skill statistics."""

    total_skills: int
    total_agents_with_skills: int
    total_relationships: int
    most_used_skills: list[dict[str, object]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class AgentSkillsResponse(BaseModel):
    """Response for agent skills."""

    agent_name: str
    skills: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
