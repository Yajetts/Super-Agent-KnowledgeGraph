"""High-level SuperAgent workflow controller."""

from __future__ import annotations

from time import perf_counter

from loguru import logger

from config.settings import get_settings
from learning.workflow_learning_engine import WorkflowLearningEngine
from memory import models as memory_models
from memory.memory_service import get_memory_service
from memory.repository import MemoryRepository
from superagent.agent_factory import AgentFactory
from superagent.agent_selector import AgentSelector
from superagent.chain_of_thought import ChainOfThought
from superagent.context_manager import ContextManager
from graph.context_builder import build_graph_context
from graph.graph_manager import GraphManager
from graph.knowledge_graph_builder import KnowledgeGraphBuilder
from graph.query_engine import GraphQueryEngine
from rag.graphrag import GraphRAGEngine
from rag.indexer import KnowledgeIndexer
from superagent.schemas import TaskAnalysis, WorkflowResult
from superagent.task_context import TaskContext
from superagent.task_analyzer import TaskAnalyzer
from services.llm_service import LLMService, get_llm_service
from dynamic_agents.capability_analyzer import CapabilityAnalyzer
from dynamic_agents.dynamic_factory import analyze_and_create_if_needed
from dynamic_agents.agent_registry import DynamicAgentRegistry
from agent_selection.relevance_matcher import RelevanceMatcher


class SuperAgentController:
    """Coordinate task analysis, agent selection, and workflow execution."""

    def __init__(
        self,
        task_analyzer: TaskAnalyzer | None = None,
        agent_selector: AgentSelector | None = None,
        agent_factory: AgentFactory | None = None,
        llm_service: LLMService | None = None,
        graph_manager: GraphManager | None = None,
        knowledge_graph_builder: KnowledgeGraphBuilder | None = None,
        knowledge_indexer: KnowledgeIndexer | None = None,
        graphrag_engine: GraphRAGEngine | None = None,
        learning_engine: WorkflowLearningEngine | None = None,
        capability_analyzer: CapabilityAnalyzer | None = None,
        relevance_matcher: RelevanceMatcher | None = None,
        chain_of_thought: ChainOfThought | None = None,
    ) -> None:
        self.task_analyzer = task_analyzer or TaskAnalyzer()
        self.agent_selector = agent_selector or AgentSelector()
        self.llm_service = llm_service or get_llm_service()
        self.agent_factory = agent_factory or AgentFactory(llm_service=self.llm_service)
        self.context_manager = ContextManager()
        settings = get_settings()
        # Disable Neo4j by default to prevent connection timeout during startup
        self.graph_manager = graph_manager or GraphManager(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            enabled=True,  # Disabled by default
        )
        self.graph_query_engine = GraphQueryEngine(self.graph_manager)
        self.knowledge_graph_builder = knowledge_graph_builder or KnowledgeGraphBuilder(self.graph_manager)
        self.knowledge_indexer = knowledge_indexer or KnowledgeIndexer()
        self.graphrag_engine = graphrag_engine or GraphRAGEngine(
            graph_query_engine=self.graph_query_engine,
        )
        self.memory_service = get_memory_service()
        self.learning_engine = learning_engine or WorkflowLearningEngine()
        self.memory_repository = MemoryRepository()
        self.capability_analyzer = capability_analyzer or CapabilityAnalyzer()
        self.dynamic_agent_registry = DynamicAgentRegistry()
        self.relevance_matcher = relevance_matcher or RelevanceMatcher()
        self.chain_of_thought = chain_of_thought or ChainOfThought()

    def analyze_task(self, query: str) -> TaskAnalysis:
        """Analyze an incoming task and return a structured summary."""
        logger.info("Task received: {}", query)
        return self.task_analyzer.analyze(query)

    def create_execution_plan(self, query: str) -> list[str]:
        """Create an ordered agent list without running any agents."""
        analysis = self.analyze_task(query)

        # Step 1: Use relevance matcher to find existing relevant agents with diverse skills
        selected_agents = []
        try:
            logger.info("Using relevance matcher for diverse agent selection")
            selected_agents_dict = self.relevance_matcher.select_agents_by_aspects(
                required_skills=analysis.required_skills,
                task_type=analysis.task_type,
                task_query=query,
            )
            selected_agents = [agent["name"] for agent in selected_agents_dict]
            logger.info("Found {} diverse relevant existing agents: {}", len(selected_agents), selected_agents)
        except Exception as exc:
            logger.warning("Relevance matcher failed, falling back to normal agent selection: {}", exc)
            selected_agents = self.agent_selector.select_agents(analysis.required_skills)

        # Step 2: Check for capability gaps and create additional agents if needed
        # Even if some agents were found, we might need to create more for comprehensive coverage
        new_agent_profiles = []
        try:
            logger.info("Running capability analysis for task: {}", query)
            capability_analysis = self.capability_analyzer.analyze_task(query)

            if capability_analysis.should_create_agent and capability_analysis.capability_gaps:
                logger.info(
                    "Capability gaps detected, attempting to create dynamic agents for gaps: {}",
                    [gap.required_skill for gap in capability_analysis.capability_gaps],
                )
                # Create agents for each significant capability gap
                for gap in capability_analysis.capability_gaps[:3]:  # Limit to 3 new agents per task
                    new_agent_profile = analyze_and_create_if_needed(query)
                    if new_agent_profile:
                        logger.info("Successfully created dynamic agent: {}", new_agent_profile.name)
                        new_agent_profiles.append(new_agent_profile)
                        # Add to selection if not already present
                        if new_agent_profile.name not in selected_agents:
                            selected_agents.append(new_agent_profile.name)
        except Exception as exc:
            logger.warning("Capability analysis failed: {}", exc)

        logger.info("Selected agents: {}", selected_agents)
        return selected_agents

    def execute_workflow(self, query: str) -> WorkflowResult:
        """Execute the selected agents sequentially and return the final result."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Query must not be empty.")

        # Start chain of thought tracking
        self.chain_of_thought.clear()
        self.chain_of_thought.start_workflow(normalized_query)

        logger.info("Task received: {}", normalized_query)
        start_time = perf_counter()
        analysis = self.analyze_task(normalized_query)

        # Record task analysis in chain of thought
        self.chain_of_thought.set_task_analysis(analysis.task_type, analysis.required_skills)

        # Step 1: Use relevance matcher to find existing relevant agents with diverse skills
        selected_agents = []
        agent_scores = []
        try:
            logger.info("Using relevance matcher for diverse agent selection")
            selected_agents_dict = self.relevance_matcher.select_agents_by_aspects(
                required_skills=analysis.required_skills,
                task_type=analysis.task_type,
                task_query=normalized_query,
            )
            selected_agents = [agent["name"] for agent in selected_agents_dict]
            
            # Calculate relevance scores for chain of thought
            all_agents = self.relevance_matcher.registry.get_all_agents()
            scored_agents = self.relevance_matcher.rank_agents(
                analysis.required_skills, analysis.task_type, normalized_query, all_agents
            )
            # Get scores for selected agents only
            selected_agent_names = set(selected_agents)
            agent_scores = [(agent["name"], score) for agent, score in scored_agents if agent["name"] in selected_agent_names]
            
            # Record agent selection in chain of thought
            self.chain_of_thought.record_agent_selection(agent_scores)
            
            logger.info("Found {} diverse relevant existing agents: {}", len(selected_agents), selected_agents)
        except Exception as exc:
            logger.warning("Relevance matcher failed, falling back to normal agent selection: {}", exc)
            selected_agents = self.agent_selector.select_agents(analysis.required_skills)

        # Step 2: Check for capability gaps and create additional agents if needed
        # Even if some agents were found, we might need to create more for comprehensive coverage
        new_agent_profiles = []
        try:
            logger.info("Running capability analysis for task: {}", normalized_query)
            capability_analysis = self.capability_analyzer.analyze_task(normalized_query)

            if capability_analysis.should_create_agent and capability_analysis.capability_gaps:
                gaps = [gap.required_skill for gap in capability_analysis.capability_gaps]
                self.chain_of_thought.record_capability_gaps(gaps)

                logger.info(
                    "Capability gaps detected, attempting to create dynamic agents for gaps: {}",
                    gaps,
                )
                # Create agents for each significant capability gap
                for gap in capability_analysis.capability_gaps[:3]:  # Limit to 3 new agents per task
                    new_agent_profile = analyze_and_create_if_needed(normalized_query)
                    if new_agent_profile:
                        # Only record if agent is actually new (not already in registry)
                        if new_agent_profile.name not in [agent["name"] for agent in self.dynamic_agent_registry.get_all_agents()]:
                            logger.info("Successfully created new dynamic agent: {}", new_agent_profile.name)
                            self.chain_of_thought.record_dynamic_agent_created(new_agent_profile.name)
                            new_agent_profiles.append(new_agent_profile)
                        # Add to selection if not already present
                        if new_agent_profile.name not in selected_agents:
                            selected_agents.append(new_agent_profile.name)
        except Exception as exc:
            logger.warning("Capability analysis failed: {}", exc)

        logger.info("Selected agents: {}", selected_agents)

        context = self.context_manager.create_context(normalized_query, analysis.task_type)
        
        # Use GraphRAG for unified context retrieval
        try:
            context.graphrag_context = self.graphrag_engine.retrieve_context(normalized_query)
            context.metadata["graphrag_context_available"] = True
            logger.info("GraphRAG context retrieved successfully")
            self.chain_of_thought.record_context_retrieval("GraphRAG", True)
        except Exception as exc:
            logger.warning("GraphRAG retrieval failed, falling back to graph context: {}", exc)
            context.graph_context = build_graph_context(normalized_query, query_engine=self.graph_query_engine)
            context.metadata["graphrag_context_available"] = False
            context.metadata["graph_context_available"] = bool(
                context.graph_context.related_tasks
                or context.graph_context.related_findings
                or context.graph_context.related_risks
                or context.graph_context.related_recommendations
            )
            self.chain_of_thought.record_context_retrieval("GraphRAG", False)
        
        context.metadata["selected_agents"] = list(selected_agents)

        agent_objects = self.agent_factory.create_agents(selected_agents)
        agent_execution_times = []

        for idx, agent in enumerate(agent_objects):
            logger.info("Agent execution start: {}", agent.name)
            self.chain_of_thought.record_agent_execution_start(agent.name)
            agent_start = perf_counter()
            context = agent.execute(context)
            context = self.context_manager.validate_context(context)
            agent_time = perf_counter() - agent_start
            agent_execution_times.append({"agent_name": agent.name, "execution_order": idx + 1, "execution_time": agent_time})
            logger.info("Agent execution completion: {} (time: {}s)", agent.name, round(agent_time, 2))
            
            # Get the agent's answer from the context
            agent_answer = ""
            if context.findings:
                agent_answer = " ".join([f.content for f in context.findings[-3:]])  # Last 3 findings
            elif context.recommendations:
                agent_answer = " ".join([r.content for r in context.recommendations[-3:]])  # Last 3 recommendations
            elif context.risks:
                agent_answer = " ".join([r.description for r in context.risks[-3:]])  # Last 3 risks
            else:
                agent_answer = "No specific output generated"
            
            self.chain_of_thought.record_agent_execution_complete(agent.name, agent_answer, agent_time)

        duration_seconds = perf_counter() - start_time
        context.metadata["execution_duration_seconds"] = round(duration_seconds, 6)
        logger.info("Execution duration: {} seconds", round(duration_seconds, 6))
        logger.info("Workflow completion summary: {}", self.context_manager.get_summary(context))

        try:
            self.knowledge_graph_builder.build_from_context(context)
        except Exception:
            logger.exception("Graph write failed; returning workflow result without persistence")

        try:
            workflow_result = WorkflowResult(
                query=context.query,
                task_type=context.task_type,
                agents_used=list(context.agent_history),
                findings=list(context.findings),
                risks=list(context.risks),
                recommendations=list(context.recommendations),
            )
            task_id = context.metadata.get("task_id") or str(context.query)
            self.knowledge_indexer.index_workflow_result(workflow_result, task_id)
        except Exception:
            logger.exception("Vector indexing failed; returning workflow result without vector persistence")
            workflow_result = WorkflowResult(
                query=context.query,
                task_type=context.task_type,
                agents_used=list(context.agent_history),
                findings=list(context.findings),
                risks=list(context.risks),
                recommendations=list(context.recommendations),
            )

        # Memory Storage
        try:
            # Get GraphRAG metadata for retrieval statistics
            graph_results_count = 0
            vector_results_count = 0
            fusion_results_count = 0
            
            if context.metadata.get("graphrag_context_available") and context.graphrag_context:
                graph_results_count = len(context.graphrag_context.graph_results) if context.graphrag_context.graph_results else 0
                vector_results_count = len(context.graphrag_context.vector_results) if context.graphrag_context.vector_results else 0
                # GraphRAGContext uses merged results instead of fusion_results
                fusion_results_count = len(context.graphrag_context.merged_findings) + len(context.graphrag_context.merged_risks) + len(context.graphrag_context.merged_recommendations)
            
            # Save workflow memory
            workflow_id = self.memory_service.record_workflow(
                query=normalized_query,
                task_type=analysis.task_type,
                execution_time=duration_seconds,
                agents_used=list(context.agent_history),
                graph_results_count=graph_results_count,
                vector_results_count=vector_results_count,
                fusion_results_count=fusion_results_count,
            )
            
            # Save agent execution memories (only if workflow was saved successfully)
            if workflow_id > 0:
                for agent_exec in agent_execution_times:
                    self.memory_service.record_agent_execution(
                        workflow_id=workflow_id,
                        agent_name=agent_exec["agent_name"],
                        execution_order=agent_exec["execution_order"],
                        execution_time=agent_exec["execution_time"],
                    )
            
            # Save retrieval memory (only if workflow was saved successfully)
            if workflow_id > 0:
                retrieval_data = {}
                if context.metadata.get("graphrag_context_available") and context.graphrag_context:
                    if context.graphrag_context.graph_results:
                        retrieval_data["graph_results"] = [r.model_dump() if hasattr(r, 'model_dump') else r for r in context.graphrag_context.graph_results]
                    if context.graphrag_context.vector_results:
                        retrieval_data["vector_results"] = [r.model_dump() if hasattr(r, 'model_dump') else r for r in context.graphrag_context.vector_results]
                    # Store merged results as fusion results
                    merged_results = {
                        "merged_findings": context.graphrag_context.merged_findings,
                        "merged_risks": context.graphrag_context.merged_risks,
                        "merged_recommendations": context.graphrag_context.merged_recommendations,
                    }
                    retrieval_data["fusion_results"] = merged_results
                
                self.memory_service.record_retrieval(
                    workflow_id=workflow_id,
                    graph_results=retrieval_data.get("graph_results"),
                    vector_results=retrieval_data.get("vector_results"),
                    fusion_results=retrieval_data.get("fusion_results"),
                )
                
                logger.info("Memory storage completed for workflow ID: {}", workflow_id)
                self.chain_of_thought.record_memory_storage(workflow_id)
        except Exception as exc:
            logger.exception("Memory storage failed; returning workflow result without memory persistence")

        # Process completed workflow through learning pipeline
        try:
            if workflow_id > 0:
                # Get workflow data within session scope to avoid binding issues
                from memory.database import get_db_manager
                db_manager = get_db_manager()
                with db_manager.session_scope() as session:
                    workflow = session.query(memory_models.WorkflowMemory).filter(
                        memory_models.WorkflowMemory.id == workflow_id
                    ).first()
                    if workflow:
                        learning_result = self.learning_engine.process_completed_workflow(workflow)
                        logger.info("Learning pipeline processing result: {}", learning_result)
                        self.chain_of_thought.record_learning_processing(str(learning_result))
        except Exception as exc:
            logger.warning("Learning pipeline processing failed: {}", exc)

        # Print the chain of thought narrative
        self.chain_of_thought.print_narrative()

        # Add execution metadata to workflow result
        workflow_result.execution_time = duration_seconds
        workflow_result.workflow_id = workflow_id if workflow_id > 0 else None
        workflow_result.chain_of_thought = self.chain_of_thought.get_narrative()

        # Format the response into user-friendly text
        workflow_result.formatted_response = self._format_workflow_result(workflow_result)

        return workflow_result

    def get_graph_context(self, query: str) -> dict[str, object]:
        """Return graph retrieval context for API consumers."""
        graph_context = build_graph_context(query, query_engine=self.graph_query_engine)
        return graph_context.model_dump()

    def get_graph_stats(self) -> dict[str, int]:
        """Return graph statistics for API consumers."""
        return self.graph_manager.get_stats()

    def get_graph_schema(self) -> dict[str, object]:
        """Return the graph schema summary with agent metadata."""
        from agents.agent_metadata import get_all_agent_metadata

        schema = self.graph_manager.get_schema_summary()
        schema["agents"] = [metadata.model_dump() for metadata in get_all_agent_metadata()]
        return schema

    def get_graphrag_context(self, query: str) -> dict[str, object]:
        """Return GraphRAG retrieval context for API consumers."""
        try:
            graphrag_context = self.graphrag_engine.retrieve_context(query)
            return graphrag_context.model_dump()
        except Exception as exc:
            logger.error("GraphRAG context retrieval failed: {}", exc)
            raise

    def get_graphrag_stats(self) -> dict[str, object]:
        """Return GraphRAG system statistics for API consumers."""
        try:
            return self.graphrag_engine.get_stats()
        except Exception as exc:
            logger.error("GraphRAG stats retrieval failed: {}", exc)
            raise

    def _format_workflow_result(self, result: WorkflowResult) -> str:
        """Format workflow result into user-friendly text."""
        formatted_parts = []

        # Add findings
        if result.findings:
            formatted_parts.append("## Findings\n")
            for idx, finding in enumerate(result.findings, 1):
                formatted_parts.append(f"{idx}. {finding.content}\n")

        # Add risks
        if result.risks:
            formatted_parts.append("\n## Risks\n")
            for idx, risk in enumerate(result.risks, 1):
                formatted_parts.append(f"{idx}. **{risk.severity}**: {risk.description}\n")

        # Add recommendations
        if result.recommendations:
            formatted_parts.append("\n## Recommendations\n")
            for idx, rec in enumerate(result.recommendations, 1):
                formatted_parts.append(f"{idx}. **{rec.priority}**: {rec.content}\n")

        # If no structured content, provide a summary
        if not formatted_parts:
            formatted_parts.append("No structured findings, risks, or recommendations were generated.")

        return "".join(formatted_parts)

    def close(self) -> None:
        """Close graph resources at application shutdown."""
        self.graph_manager.close()
