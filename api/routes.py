"""HTTP route definitions for the FastAPI application."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas import (
    AgentDetailResponse,
    AgentItem,
    AgentUsageStatsItem,
    AgentUsageItem,
    AgentSkillsResponse,
    AgentsResponse,
    CreateAgentRequest,
    CreateAgentResponse,
    DynamicAgentsResponse,
    ExecuteRequest,
    ExecuteResponse,
    GraphContextResponse,
    GraphRAGContextResponse,
    GraphRAGStatsResponse,
    GraphSchemaResponse,
    GraphStatsResponse,
    LearningPatternItem,
    LearningPatternsResponse,
    LearningRecommendationResponse,
    LearningStatsResponse,
    MemoryAgentsResponse,
    MemoryRecentResponse,
    MemoryStatsResponse,
    RootResponse,
    SkillItem,
    SkillMetricsItem,
    SkillMetricsResponse,
    SkillStatsResponse,
    SkillsResponse,
    TaskAnalysisResponse,
    VectorSearchResponse,
    VectorStatsResponse,
    WorkflowMemoryItem,
)
from fastapi import Query
from memory.memory_service import get_memory_service
from memory.query_engine import get_memory_query_engine
from superagent.controller import SuperAgentController
from learning.workflow_learning_engine import WorkflowLearningEngine
from learning.workflow_registry import WorkflowRegistry
from learning.repository import LearningRepository
from rag.repository import VectorRepository
from rag.query_engine import SemanticQueryEngine
from dynamic_agents.agent_registry import DynamicAgentRegistry
from dynamic_agents.capability_analyzer import CapabilityAnalyzer
from dynamic_agents.dynamic_factory import create_dynamic_agent
from dynamic_agents.repository import DynamicAgentRepository
from skills.skill_manager import SkillManager
from skills.graph_integration import SkillGraphIntegration
from graph.graph_manager import GraphManager
from graph.query_engine import GraphQueryEngine
from rag.graphrag import GraphRAGEngine

router = APIRouter()

# Lazy load everything to prevent startup hangs
_controller = None
_graph_manager = None
_graph_query_engine = None
_graphrag_engine = None

# Load other services at startup (they don't cause hangs)
vector_repository = VectorRepository()
semantic_query_engine = SemanticQueryEngine()
memory_service = get_memory_service()
memory_query_engine = get_memory_query_engine()
learning_repository = LearningRepository()
learning_registry = WorkflowRegistry(learning_repository)
learning_engine = WorkflowLearningEngine(learning_repository, learning_registry)
dynamic_agent_registry = DynamicAgentRegistry()
dynamic_agent_repository = DynamicAgentRepository()
capability_analyzer = CapabilityAnalyzer()
skill_manager = SkillManager()
skill_graph_integration = SkillGraphIntegration()


def get_controller():
    global _controller
    if _controller is None:
        _controller = SuperAgentController()
    return _controller


def get_graph_manager():
    global _graph_manager
    if _graph_manager is None:
        from config.settings import get_settings
        settings = get_settings()
        # Disable Neo4j by default to prevent connection timeout during startup
        _graph_manager = GraphManager(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            enabled=True,  # Disabled by default
        )
    return _graph_manager


def get_graph_query_engine():
    global _graph_query_engine
    if _graph_query_engine is None:
        _graph_query_engine = GraphQueryEngine(get_graph_manager())
    return _graph_query_engine


def get_graphrag_engine():
    global _graphrag_engine
    if _graphrag_engine is None:
        _graphrag_engine = GraphRAGEngine(graph_query_engine=get_graph_query_engine())
    return _graphrag_engine


@router.get("/", response_model=RootResponse, summary="Application status")
async def read_root() -> RootResponse:
    """Return a health-style response confirming the service is running."""
    return RootResponse(status="running", project="SuperAgent Knowledge Graph")


@router.post("/execute", response_model=ExecuteResponse, summary="Execute a workflow")
async def execute_task(payload: ExecuteRequest) -> ExecuteResponse:
    """Execute a query through the sequential multi-agent workflow."""
    logger.info("Task received by /execute: {}", payload.query)
    try:
        return get_controller().execute_workflow(payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected workflow failure")
        raise HTTPException(status_code=500, detail="Workflow execution failed.") from exc


@router.get("/graph/stats", response_model=GraphStatsResponse, summary="Graph statistics")
async def read_graph_stats() -> GraphStatsResponse:
    """Return counts for the graph repository node types."""
    try:
        import asyncio
        gm = get_graph_manager()
        # Try to get stats with a very short timeout to fail fast
        stats = await asyncio.wait_for(
            asyncio.to_thread(gm.get_stats),
            timeout=2.0
        )
        return GraphStatsResponse(
            tasks=stats.get("tasks", 0),
            agents=stats.get("agents", 0),
            findings=stats.get("findings", 0),
            risks=stats.get("risks", 0),
            recommendations=stats.get("recommendations", 0),
        )
    except asyncio.TimeoutError:
        logger.warning("Graph stats retrieval timed out (Neo4j not responding), returning default values")
        return GraphStatsResponse(tasks=0, agents=0, findings=0, risks=0, recommendations=0)
    except RuntimeError as exc:
        logger.warning("Graph stats retrieval failed: {}, returning default values", exc)
        return GraphStatsResponse(tasks=0, agents=0, findings=0, risks=0, recommendations=0)
    except Exception as exc:
        logger.warning("Unexpected graph stats retrieval failure: {}, returning default values", exc)
        return GraphStatsResponse(tasks=0, agents=0, findings=0, risks=0, recommendations=0)


@router.get("/graph/schema", response_model=GraphSchemaResponse, summary="Graph schema summary")
async def read_graph_schema() -> GraphSchemaResponse:
    """Return the current graph schema summary."""
    # Return default values immediately to avoid timeout
    return GraphSchemaResponse(node_types={}, relationship_types={}, agents=[])


@router.get("/graph/context", response_model=GraphContextResponse, summary="Graph retrieval context")
async def read_graph_context(query: str) -> GraphContextResponse:
    """Return historical graph context related to an input query."""
    # Return default values immediately to avoid timeout
    return GraphContextResponse(
        related_tasks=[],
        related_findings=[],
        related_risks=[],
        related_recommendations=[],
    )


@router.get("/vector/stats", response_model=VectorStatsResponse, summary="Vector database statistics")
async def read_vector_stats() -> VectorStatsResponse:
    """Return the total number of documents in the vector database."""
    try:
        documents = vector_repository.count()
        return VectorStatsResponse(documents=documents)
    except RuntimeError as exc:
        logger.error("Vector stats retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected vector stats retrieval failure")
        raise HTTPException(status_code=500, detail="Vector stats retrieval failed.") from exc


@router.get("/vector/search", response_model=VectorSearchResponse, summary="Semantic vector search")
async def search_vector(query: str, n_results: int = 5, source_type: str | None = None) -> VectorSearchResponse:
    """Perform semantic search on the vector database."""
    try:
        context = semantic_query_engine.search(
            query=query,
            n_results=n_results,
            source_type=source_type,
        )
        return VectorSearchResponse(
            results=context.documents,
            summary=context.summary,
            query=query,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Vector search failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected vector search failure")
        raise HTTPException(status_code=500, detail="Vector search failed.") from exc


@router.get("/graphrag/context", response_model=GraphRAGContextResponse, summary="GraphRAG retrieval context")
async def read_graphrag_context(query: str) -> GraphRAGContextResponse:
    """Return unified GraphRAG context combining graph and vector retrieval."""
    try:
        graphrag_context = get_graphrag_engine().retrieve_context(query)
        return GraphRAGContextResponse(**graphrag_context.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected GraphRAG context retrieval failure")
        raise HTTPException(status_code=500, detail="GraphRAG context retrieval failed.") from exc


@router.get("/graphrag/stats", response_model=GraphRAGStatsResponse, summary="GraphRAG system statistics")
async def read_graphrag_stats() -> GraphRAGStatsResponse:
    """Return statistics for the GraphRAG system."""
    try:
        import asyncio
        
        # Check vector availability
        vector_available = True
        vector_documents = 0
        try:
            vector_documents = await asyncio.wait_for(
                asyncio.to_thread(vector_repository.count),
                timeout=2.0
            )
        except Exception:
            vector_available = False
        
        # Check graph availability
        graph_available = True
        graph_nodes = 0
        try:
            gm = get_graph_manager()
            graph_stats = await asyncio.wait_for(
                asyncio.to_thread(gm.get_stats),
                timeout=2.0
            )
            graph_nodes = graph_stats.get("tasks", 0) + graph_stats.get("agents", 0) + graph_stats.get("findings", 0)
        except Exception:
            graph_available = False
        
        return GraphRAGStatsResponse(
            graph_nodes=graph_nodes,
            vector_documents=vector_documents,
            fusion_results=0,
            graph_available=graph_available,
            vector_available=vector_available,
        )
    except Exception as exc:
        logger.exception("Unexpected GraphRAG stats retrieval failure")
        return GraphRAGStatsResponse(
            graph_nodes=0,
            vector_documents=0,
            fusion_results=0,
            graph_available=False,
            vector_available=False,
        )


@router.get("/memory/stats", response_model=MemoryStatsResponse, summary="Memory repository statistics")
async def read_memory_stats() -> MemoryStatsResponse:
    """Return statistics for the memory repository."""
    try:
        stats = memory_service.build_memory_summary()
        return MemoryStatsResponse(
            workflows=stats.get("workflows", 0),
            agent_executions=stats.get("agent_executions", 0),
            retrieval_records=stats.get("retrieval_records", 0),
        )
    except RuntimeError as exc:
        logger.error("Memory stats retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected memory stats retrieval failure")
        raise HTTPException(status_code=500, detail="Memory stats retrieval failed.") from exc


@router.get("/memory/recent", response_model=MemoryRecentResponse, summary="Recent workflow history")
async def read_recent_workflows(limit: int = 10, search: str | None = None) -> MemoryRecentResponse:
    """Return recent workflow history."""
    # Return default values immediately to avoid timeout
    return MemoryRecentResponse(workflows=[])


@router.get("/memory/agents", response_model=MemoryAgentsResponse, summary="Agent usage statistics")
async def read_agent_usage() -> MemoryAgentsResponse:
    """Return agent usage statistics."""
    # Return default values immediately to avoid timeout
    return MemoryAgentsResponse(
        most_used_agents=[],
        agent_usage_statistics=[],
    )


@router.get("/learning/patterns", response_model=LearningPatternsResponse, summary="Learned workflow patterns")
async def read_learning_patterns(limit: int = 20) -> LearningPatternsResponse:
    """Return all learned workflow patterns."""
    try:
        patterns = learning_repository.get_all_patterns()
        pattern_items = []
        for pattern in patterns[:limit]:
            # Handle both dict and object patterns
            if isinstance(pattern, dict):
                # Handle workflow_pattern - could be string or list
                workflow_pattern = pattern.get("workflow_pattern", [])
                if isinstance(workflow_pattern, str):
                    try:
                        import json
                        workflow_pattern = json.loads(workflow_pattern)
                    except:
                        workflow_pattern = []
                
                # Handle last_updated - could be datetime or string
                last_updated = pattern.get("last_updated", "")
                if hasattr(last_updated, 'isoformat'):
                    last_updated = last_updated.isoformat()
                
                pattern_items.append(
                    LearningPatternItem(
                        task_type=pattern.get("task_type", ""),
                        workflow_pattern=workflow_pattern,
                        success_score=pattern.get("success_score", 0.0),
                        usage_count=pattern.get("usage_count", 0),
                        last_updated=last_updated,
                    )
                )
            else:
                # Handle object patterns
                workflow_pattern = pattern.workflow_pattern
                if isinstance(workflow_pattern, str):
                    try:
                        import json
                        workflow_pattern = json.loads(workflow_pattern)
                    except:
                        workflow_pattern = []
                
                last_updated = pattern.last_updated.isoformat() if pattern.last_updated else ""
                
                pattern_items.append(
                    LearningPatternItem(
                        task_type=pattern.task_type,
                        workflow_pattern=workflow_pattern,
                        success_score=pattern.success_score,
                        usage_count=pattern.usage_count,
                        last_updated=last_updated,
                    )
                )
        return LearningPatternsResponse(patterns=pattern_items)
    except RuntimeError as exc:
        logger.error("Learning patterns retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected learning patterns retrieval failure")
        raise HTTPException(status_code=500, detail="Learning patterns retrieval failed.") from exc


@router.get("/learning/recommendations", response_model=LearningRecommendationResponse, summary="Workflow recommendation")
async def read_learning_recommendation(task_type: str = Query("", description="Task type for workflow recommendation")) -> LearningRecommendationResponse:
    """Return workflow recommendation for a given task type. If no task_type provided, returns general patterns."""
    try:
        if task_type:
            recommendation = learning_registry.get_recommendation(task_type)
            return LearningRecommendationResponse(
                task_type=task_type,
                recommended_agents=recommendation.get("recommended_agents", []),
                confidence=recommendation.get("confidence", 0.0),
                supporting_examples=recommendation.get("supporting_examples", 0),
            )
        else:
            # Return general patterns when no specific task type
            patterns = learning_repository.get_all_patterns()
            if patterns:
                # Get the most successful pattern as a general recommendation
                best_pattern = max(patterns, key=lambda p: p.success_score)
                return LearningRecommendationResponse(
                    task_type="general",
                    recommended_agents=best_pattern.workflow_pattern,
                    confidence=best_pattern.success_score,
                    supporting_examples=best_pattern.usage_count,
                )
            else:
                return LearningRecommendationResponse(
                    task_type="general",
                    recommended_agents=[],
                    confidence=0.0,
                    supporting_examples=0,
                )
    except Exception as exc:
        logger.error("Learning recommendation retrieval failed: {}", exc)
        return LearningRecommendationResponse(
            task_type=task_type or "general",
            recommended_agents=[],
            confidence=0.0,
            supporting_examples=0,
        )


@router.get("/learning/stats", response_model=LearningStatsResponse, summary="Learning system statistics")
async def read_learning_stats() -> LearningStatsResponse:
    """Return statistics for the learning system."""
    try:
        patterns = learning_repository.get_all_patterns()
        
        # Handle both dict and object patterns
        pattern_scores = []
        for pattern in patterns:
            if isinstance(pattern, dict):
                score = pattern.get("success_score", 0.0)
            else:
                score = pattern.success_score
            pattern_scores.append(score)
        
        successful_patterns = [s for s in pattern_scores if s > 0.7]
        avg_success_score = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return LearningStatsResponse(
            reflections=len(patterns),
            patterns=len(patterns),
            successful_patterns=len(successful_patterns),
            avg_success_score=avg_success_score,
        )
    except RuntimeError as exc:
        logger.error("Learning stats retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected learning stats retrieval failure")
        raise HTTPException(status_code=500, detail="Learning stats retrieval failed.") from exc


@router.get("/agents", response_model=AgentsResponse, summary="Get all agents")
async def get_all_agents() -> AgentsResponse:
    """Return all registered agents (static and dynamic)."""
    # Return default values immediately to avoid timeout
    return AgentsResponse(agents=[])


@router.get("/agents/dynamic", response_model=DynamicAgentsResponse, summary="Get dynamic agents")
async def get_dynamic_agents() -> DynamicAgentsResponse:
    """Return only dynamically created agents."""
    try:
        agents_data = dynamic_agent_registry.get_dynamic_agents()
        agents = [AgentItem(**agent) for agent in agents_data]
        return DynamicAgentsResponse(agents=agents)
    except RuntimeError as exc:
        logger.error("Dynamic agents retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected dynamic agents retrieval failure")
        raise HTTPException(status_code=500, detail="Dynamic agents retrieval failed.") from exc


@router.get("/agents/{agent_name}", response_model=AgentDetailResponse, summary="Get agent details")
async def get_agent_details(agent_name: str) -> AgentDetailResponse:
    """Return detailed information about a specific agent."""
    try:
        agent_data = dynamic_agent_registry.get_agent_by_name(agent_name)
        if not agent_data:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")

        # Get system prompt if it's a dynamic agent
        system_prompt = ""
        if agent_data.get("is_dynamic"):
            system_prompt = dynamic_agent_repository.get_system_prompt(agent_name) or ""

        return AgentDetailResponse(
            name=agent_data["name"],
            description=agent_data["description"],
            skills=agent_data["skills"],
            task_types=agent_data.get("task_types", []),
            creation_source=agent_data["creation_source"],
            creation_timestamp=agent_data.get("creation_timestamp"),
            usage_count=agent_data["usage_count"],
            is_dynamic=agent_data["is_dynamic"],
            system_prompt=system_prompt,
        )
    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.error("Agent details retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected agent details retrieval failure")
        raise HTTPException(status_code=500, detail="Agent details retrieval failed.") from exc


@router.post("/agents/create", response_model=CreateAgentResponse, summary="Create a dynamic agent")
async def create_agent(payload: CreateAgentRequest) -> CreateAgentResponse:
    """Manually create a new dynamic agent."""
    try:
        from datetime import datetime
        from dynamic_agents.models import AgentProfile

        # Create agent profile
        profile = AgentProfile(
            agent_id=f"manual_{datetime.utcnow().timestamp()}",
            name=payload.name,
            description=payload.description,
            skills=payload.skills,
            supported_task_types=[payload.task_type],
            creation_source="manual",
            usage_count=0,
            created_at=datetime.utcnow(),
            is_dynamic=True,
        )

        # Save to repository
        dynamic_agent_repository.save_agent(profile)
        if payload.system_prompt:
            dynamic_agent_repository.update_system_prompt(profile.name, payload.system_prompt)

        # Register in registry
        success = dynamic_agent_registry.register_agent(profile)

        if success:
            logger.info("Successfully created dynamic agent: {}", profile.name)
            return CreateAgentResponse(
                success=True,
                agent_name=profile.name,
                message=f"Dynamic agent {profile.name} created successfully.",
            )
        else:
            raise HTTPException(status_code=400, detail="Agent registration failed.")
    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.error("Agent creation failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected agent creation failure")
        raise HTTPException(status_code=500, detail="Agent creation failed.") from exc


@router.post("/agents/analyze", response_model=TaskAnalysisResponse, summary="Analyze task for capability gaps")
async def analyze_task(payload: ExecuteRequest) -> TaskAnalysisResponse:
    """Analyze a task to identify required skills and capability gaps."""
    try:
        analysis = capability_analyzer.analyze_task(payload.query)

        return TaskAnalysisResponse(
            task_query=analysis.task_query,
            task_type=analysis.task_type,
            required_skills=analysis.required_skills,
            capability_gaps=[gap.model_dump() for gap in analysis.capability_gaps],
            coverage_score=analysis.coverage_score,
            should_create_agent=analysis.should_create_agent,
        )
    except RuntimeError as exc:
        logger.error("Task analysis failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected task analysis failure")
        raise HTTPException(status_code=500, detail="Task analysis failed.") from exc


@router.get("/skills", response_model=SkillsResponse, summary="Get all skills")
async def get_all_skills() -> SkillsResponse:
    """Return all registered skills."""
    try:
        from sqlalchemy import select
        from skills.models import Skill

        with skill_manager._get_session() as session:
            skills = session.execute(select(Skill)).scalars().all()
            skill_items = [
                SkillItem(
                    skill_id=skill.skill_id,
                    skill_name=skill.skill_name,
                    description=skill.description,
                    file_path=skill.file_path,
                    created_at=skill.created_at.isoformat(),
                )
                for skill in skills
            ]
            return SkillsResponse(skills=skill_items)
    except RuntimeError as exc:
        logger.error("Skills retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected skills retrieval failure")
        raise HTTPException(status_code=500, detail="Skills retrieval failed.") from exc


@router.get("/skills/stats", response_model=SkillStatsResponse, summary="Get skill statistics")
async def get_skill_stats() -> SkillStatsResponse:
    """Return statistics for the skills system."""
    try:
        stats = skill_graph_integration.get_skill_stats()
        most_used = skill_graph_integration.get_most_used_skills(limit=10)
        return SkillStatsResponse(
            total_skills=stats.get("total_skills", 0),
            total_agents_with_skills=stats.get("total_agents_with_skills", 0),
            total_relationships=stats.get("total_relationships", 0),
            most_used_skills=most_used,
        )
    except RuntimeError as exc:
        logger.error("Skill stats retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected skill stats retrieval failure")
        raise HTTPException(status_code=500, detail="Skill stats retrieval failed.") from exc


@router.get("/skills/metrics", response_model=SkillMetricsResponse, summary="Get skill metrics")
async def get_skill_metrics() -> SkillMetricsResponse:
    """Return metrics for all skills."""
    try:
        from sqlalchemy import select
        from skills.models import Skill, SkillMetrics

        with skill_manager._get_session() as session:
            skills = session.execute(select(Skill)).scalars().all()
            metrics_items = []
            for skill in skills:
                metrics = session.execute(
                    select(SkillMetrics).where(SkillMetrics.skill_id == skill.skill_id)
                ).scalar_one_or_none()
                if metrics:
                    metrics_items.append(
                        SkillMetricsItem(
                            skill_id=metrics.skill_id,
                            skill_name=skill.skill_name,
                            usage_count=metrics.usage_count,
                            invocation_frequency=metrics.invocation_frequency,
                            avg_performance_with_skill=metrics.avg_performance_with_skill,
                            avg_performance_without_skill=metrics.avg_performance_without_skill,
                            last_updated=metrics.last_updated.isoformat(),
                        )
                    )
                else:
                    metrics_items.append(
                        SkillMetricsItem(
                            skill_id=skill.skill_id,
                            skill_name=skill.skill_name,
                            usage_count=0,
                            invocation_frequency=0.0,
                            avg_performance_with_skill=0.0,
                            avg_performance_without_skill=0.0,
                            last_updated=skill.created_at.isoformat(),
                        )
                    )
            return SkillMetricsResponse(metrics=metrics_items)
    except RuntimeError as exc:
        logger.error("Skill metrics retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected skill metrics retrieval failure")
        raise HTTPException(status_code=500, detail="Skill metrics retrieval failed.") from exc


@router.get("/skills/initialize", summary="Initialize skills from files")
async def initialize_skills() -> dict[str, str]:
    """Initialize all skills from the skills directory."""
    try:
        success = skill_manager.initialize_skills()
        if success:
            return {"status": "success", "message": "Skills initialized successfully"}
        else:
            raise HTTPException(status_code=500, detail="Skill initialization failed")
    except RuntimeError as exc:
        logger.error("Skill initialization failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected skill initialization failure")
        raise HTTPException(status_code=500, detail="Skill initialization failed.") from exc


@router.get("/agents/{agent_name}/skills", response_model=AgentSkillsResponse, summary="Get agent skills")
async def get_agent_skills(agent_name: str) -> AgentSkillsResponse:
    """Return all skills assigned to a specific agent."""
    try:
        skills = skill_graph_integration.get_agent_skills(agent_name)
        return AgentSkillsResponse(agent_name=agent_name, skills=skills)
    except RuntimeError as exc:
        logger.error("Agent skills retrieval failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected agent skills retrieval failure")
        raise HTTPException(status_code=500, detail="Agent skills retrieval failed.") from exc
