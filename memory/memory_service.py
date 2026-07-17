"""Service layer for memory operations with business logic."""

from __future__ import annotations

from typing import Any

from loguru import logger

from memory.models import AgentExecutionMemory, WorkflowMemory
from memory.repository import MemoryRepository


class MemoryService:
    """High-level service for memory operations."""

    def __init__(self) -> None:
        """Initialize memory service with repository."""
        self.repository = MemoryRepository()

    def record_workflow(
        self,
        query: str,
        task_type: str,
        execution_time: float,
        agents_used: list[str],
        graph_results_count: int = 0,
        vector_results_count: int = 0,
        fusion_results_count: int = 0,
    ) -> int:
        """Record a workflow execution."""
        try:
            workflow_id = self.repository.save_workflow(
                query=query,
                task_type=task_type,
                execution_time=execution_time,
                agents_used=agents_used,
                graph_results_count=graph_results_count,
                vector_results_count=vector_results_count,
                fusion_results_count=fusion_results_count,
            )
            logger.info("Workflow recorded successfully with ID: {}", workflow_id)
            return workflow_id
        except Exception as exc:
            logger.error("Failed to record workflow: {}", exc)
            raise

    def record_agent_execution(
        self,
        workflow_id: int,
        agent_name: str,
        execution_order: int,
        execution_time: float,
    ) -> int:
        """Record an agent execution."""
        try:
            agent_execution_id = self.repository.save_agent_execution(
                workflow_id=workflow_id,
                agent_name=agent_name,
                execution_order=execution_order,
                execution_time=execution_time,
            )
            logger.info("Agent execution recorded successfully with ID: {}", agent_execution_id)
            return agent_execution_id
        except Exception as exc:
            logger.error("Failed to record agent execution: {}", exc)
            raise

    def record_retrieval(
        self,
        workflow_id: int,
        graph_results: dict[str, Any] | None = None,
        vector_results: dict[str, Any] | None = None,
        fusion_results: dict[str, Any] | None = None,
    ) -> int:
        """Record retrieval metadata."""
        try:
            retrieval_id = self.repository.save_retrieval(
                workflow_id=workflow_id,
                graph_results=graph_results,
                vector_results=vector_results,
                fusion_results=fusion_results,
            )
            logger.info("Retrieval recorded successfully with ID: {}", retrieval_id)
            return retrieval_id
        except Exception as exc:
            logger.error("Failed to record retrieval: {}", exc)
            raise

    def get_recent_memories(self, limit: int = 10) -> list[WorkflowMemory]:
        """Retrieve recent workflow memories."""
        try:
            workflows = self.repository.get_recent_workflows(limit=limit)
            logger.info("Retrieved {} recent memories", len(workflows))
            return workflows
        except Exception as exc:
            logger.error("Failed to retrieve recent memories: {}", exc)
            raise

    def build_memory_summary(self) -> dict[str, Any]:
        """Build a summary of memory statistics."""
        try:
            workflow_count = self.repository.get_workflow_count()
            agent_execution_count = self.repository.get_agent_execution_count()
            retrieval_count = self.repository.get_retrieval_count()

            summary = {
                "workflows": workflow_count,
                "agent_executions": agent_execution_count,
                "retrieval_records": retrieval_count,
            }
            logger.info("Memory summary built: {}", summary)
            return summary
        except Exception as exc:
            logger.error("Failed to build memory summary: {}", exc)
            raise

    def store_dynamic_agent_event(self, event_data: dict[str, Any]) -> bool:
        """Store a dynamic agent event in memory.

        Args:
            event_data: Dictionary containing event information.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # For now, we'll store these as a special workflow entry
            # This is a simplified approach - in production, you might want a separate table
            event_type = event_data.get("event_type", "unknown")
            agent_name = event_data.get("agent_name", "system")

            # Create a descriptive query for the event
            query = f"Dynamic Agent Event: {event_type} - {agent_name}"

            # Record as a workflow with special task type
            workflow_id = self.repository.save_workflow(
                query=query,
                task_type=f"dynamic_agent_{event_type}",
                execution_time=0.0,
                agents_used=[agent_name] if agent_name else [],
                graph_results_count=0,
                vector_results_count=0,
                fusion_results_count=0,
            )

            logger.info("Dynamic agent event stored with workflow ID: {}", workflow_id)
            return True
        except Exception as exc:
            logger.error("Failed to store dynamic agent event: {}", exc)
            return False

    def get_dynamic_agent_events(self, event_type: str | None = None) -> list[dict[str, Any]]:
        """Retrieve dynamic agent events from memory.

        Args:
            event_type: Optional event type to filter by.

        Returns:
            List of event dictionaries.
        """
        try:
            # Query workflows with dynamic agent task types
            workflows = self.repository.get_workflows_by_task_type_prefix("dynamic_agent_")

            events = []
            for workflow in workflows:
                event_data = {
                    "event_type": workflow.task_type.replace("dynamic_agent_", ""),
                    "timestamp": workflow.timestamp.isoformat(),
                    "query": workflow.query,
                    "agents_used": workflow.agents_used,
                }
                events.append(event_data)

            if event_type:
                events = [e for e in events if e.get("event_type") == event_type]

            return events
        except Exception as exc:
            logger.error("Failed to retrieve dynamic agent events: {}", exc)
            return []


# Global memory service instance
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Get or create the global memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
