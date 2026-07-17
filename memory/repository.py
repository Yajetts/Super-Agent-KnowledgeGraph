"""Repository layer for memory persistence operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from memory.database import get_db_manager
from memory.models import AgentExecutionMemory, RetrievalMemory, WorkflowMemory


class MemoryRepository:
    """Handle database operations for memory records."""

    def __init__(self) -> None:
        """Initialize repository with database manager."""
        self.db_manager = get_db_manager()

    def save_workflow(
        self,
        query: str,
        task_type: str,
        execution_time: float,
        agents_used: list[str],
        graph_results_count: int = 0,
        vector_results_count: int = 0,
        fusion_results_count: int = 0,
    ) -> int:
        """Save a workflow execution record and return its ID."""
        try:
            import json

            with self.db_manager.session_scope() as session:
                workflow = WorkflowMemory(
                    query=query,
                    task_type=task_type,
                    execution_time=execution_time,
                    agents_used=json.dumps(agents_used),
                    graph_results_count=graph_results_count,
                    vector_results_count=vector_results_count,
                    fusion_results_count=fusion_results_count,
                )
                session.add(workflow)
                session.flush()
                workflow_id = workflow.id
                logger.info("Workflow memory saved with ID: {}", workflow_id)
                return workflow_id
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, skipping workflow storage")
                return 0
            logger.error("Failed to save workflow memory: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to save workflow memory: {}", exc)
            raise

    def save_agent_execution(
        self,
        workflow_id: int,
        agent_name: str,
        execution_order: int,
        execution_time: float,
    ) -> int:
        """Save an agent execution record and return its ID."""
        try:
            with self.db_manager.session_scope() as session:
                agent_execution = AgentExecutionMemory(
                    workflow_id=workflow_id,
                    agent_name=agent_name,
                    execution_order=execution_order,
                    execution_time=execution_time,
                )
                session.add(agent_execution)
                session.flush()
                agent_execution_id = agent_execution.id
                logger.info("Agent execution saved with ID: {} for workflow: {}", agent_execution_id, workflow_id)
                return agent_execution_id
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, skipping agent execution storage")
                return 0
            logger.error("Failed to save agent execution: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to save agent execution: {}", exc)
            raise

    def save_retrieval(
        self,
        workflow_id: int,
        graph_results: dict[str, Any] | None = None,
        vector_results: dict[str, Any] | None = None,
        fusion_results: dict[str, Any] | None = None,
    ) -> int:
        """Save retrieval metadata and return its ID."""
        try:
            import json

            with self.db_manager.session_scope() as session:
                retrieval = RetrievalMemory(
                    workflow_id=workflow_id,
                    graph_results=json.dumps(graph_results) if graph_results else None,
                    vector_results=json.dumps(vector_results) if vector_results else None,
                    fusion_results=json.dumps(fusion_results) if fusion_results else None,
                )
                session.add(retrieval)
                session.flush()
                retrieval_id = retrieval.id
                logger.info("Retrieval memory saved with ID: {} for workflow: {}", retrieval_id, workflow_id)
                return retrieval_id
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, skipping retrieval storage")
                return 0
            logger.error("Failed to save retrieval memory: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to save retrieval memory: {}", exc)
            raise

    def get_workflow(self, workflow_id: int) -> WorkflowMemory | None:
        """Retrieve a workflow by ID."""
        try:
            with self.db_manager.session_scope() as session:
                workflow = session.query(WorkflowMemory).filter(WorkflowMemory.id == workflow_id).first()
                return workflow
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning None for workflow")
                return None
            logger.error("Failed to retrieve workflow: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve workflow: {}", exc)
            raise

    def get_recent_workflows(self, limit: int = 10) -> list[WorkflowMemory]:
        """Retrieve recent workflow records."""
        try:
            with self.db_manager.session_scope() as session:
                workflows = (
                    session.query(WorkflowMemory)
                    .order_by(WorkflowMemory.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                return workflows
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning empty list for recent workflows")
                return []
            logger.error("Failed to retrieve recent workflows: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve recent workflows: {}", exc)
            raise

    def get_agent_history(self, agent_name: str, limit: int = 50) -> list[AgentExecutionMemory]:
        """Retrieve execution history for a specific agent."""
        try:
            with self.db_manager.session_scope() as session:
                executions = (
                    session.query(AgentExecutionMemory)
                    .filter(AgentExecutionMemory.agent_name == agent_name)
                    .order_by(AgentExecutionMemory.id.desc())
                    .limit(limit)
                    .all()
                )
                return executions
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning empty list for agent history")
                return []
            logger.error("Failed to retrieve agent history: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve agent history: {}", exc)
            raise

    def get_workflow_count(self) -> int:
        """Get total number of workflows."""
        try:
            with self.db_manager.session_scope() as session:
                count = session.query(WorkflowMemory).count()
                return count
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning 0 for workflow count")
                return 0
            logger.error("Failed to get workflow count: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get workflow count: {}", exc)
            raise

    def get_agent_execution_count(self) -> int:
        """Get total number of agent executions."""
        try:
            with self.db_manager.session_scope() as session:
                count = session.query(AgentExecutionMemory).count()
                return count
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning 0 for agent execution count")
                return 0
            logger.error("Failed to get agent execution count: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get agent execution count: {}", exc)
            raise

    def get_retrieval_count(self) -> int:
        """Get total number of retrieval records."""
        try:
            with self.db_manager.session_scope() as session:
                count = session.query(RetrievalMemory).count()
                return count
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning 0 for retrieval count")
                return 0
            logger.error("Failed to get retrieval count: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get retrieval count: {}", exc)
            raise

    def get_workflows_by_task_type_prefix(self, prefix: str) -> list[WorkflowMemory]:
        """Retrieve workflows with task type starting with a given prefix."""
        try:
            with self.db_manager.session_scope() as session:
                workflows = (
                    session.query(WorkflowMemory)
                    .filter(WorkflowMemory.task_type.like(f"{prefix}%"))
                    .order_by(WorkflowMemory.timestamp.desc())
                    .all()
                )
                return workflows
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning empty list for workflows by prefix")
                return []
            logger.error("Failed to retrieve workflows by prefix: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve workflows by prefix: {}", exc)
            raise
