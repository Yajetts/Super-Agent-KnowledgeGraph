"""Memory integration for dynamic agent events."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from dynamic_agents.models import AgentProfile
from memory.memory_service import MemoryService, get_memory_service


class DynamicAgentMemoryIntegration:
    """Handles memory operations for dynamic agent events."""

    def __init__(self, memory_service: MemoryService | None = None) -> None:
        """Initialize the memory integration.

        Args:
            memory_service: Memory service instance. If None, uses default.
        """
        self.memory_service = memory_service or get_memory_service()

    def store_agent_creation_event(
        self,
        profile: AgentProfile,
        task_query: str,
        task_type: str,
        required_skills: list[str],
    ) -> bool:
        """Store an agent creation event in memory.

        Args:
            profile: Agent profile that was created.
            task_query: Task that triggered creation.
            task_type: Type of task.
            required_skills: Skills that were required.

        Returns:
            True if successful, False otherwise.
        """
        try:
            event_data = {
                "event_type": "agent_creation",
                "agent_name": profile.name,
                "agent_id": profile.agent_id,
                "timestamp": profile.created_at.isoformat(),
                "task_query": task_query,
                "task_type": task_type,
                "required_skills": required_skills,
                "agent_skills": profile.skills,
                "creation_source": profile.creation_source,
            }

            # Store as a special memory entry
            # We'll use the memory service's workflow storage mechanism
            # with a special marker for dynamic agent events
            self.memory_service.store_dynamic_agent_event(event_data)

            logger.info("Stored agent creation event in memory: {}", profile.name)
            return True

        except Exception as exc:
            logger.error("Failed to store agent creation event: {}", exc)
            return False

    def store_agent_usage_event(
        self,
        agent_name: str,
        task_id: str,
        task_query: str,
        execution_time: float,
        success: bool,
    ) -> bool:
        """Store an agent usage event in memory.

        Args:
            agent_name: Name of the agent used.
            task_id: ID of the task.
            task_query: Task query.
            execution_time: Time taken to execute.
            success: Whether execution was successful.

        Returns:
            True if successful, False otherwise.
        """
        try:
            event_data = {
                "event_type": "agent_usage",
                "agent_name": agent_name,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "task_query": task_query,
                "execution_time": execution_time,
                "success": success,
            }

            self.memory_service.store_dynamic_agent_event(event_data)

            logger.debug("Stored agent usage event for: {}", agent_name)
            return True

        except Exception as exc:
            logger.error("Failed to store agent usage event: {}", exc)
            return False

    def store_agent_success_metrics(
        self,
        agent_name: str,
        task_type: str,
        success_score: float,
        usage_count: int,
    ) -> bool:
        """Store agent success metrics for learning.

        Args:
            agent_name: Name of the agent.
            task_type: Type of task.
            success_score: Success score (0.0-1.0).
            usage_count: Total usage count.

        Returns:
            True if successful, False otherwise.
        """
        try:
            metrics_data = {
                "event_type": "agent_success_metrics",
                "agent_name": agent_name,
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat(),
                "success_score": success_score,
                "usage_count": usage_count,
            }

            self.memory_service.store_dynamic_agent_event(metrics_data)

            logger.info("Stored success metrics for agent: {}", agent_name)
            return True

        except Exception as exc:
            logger.error("Failed to store agent success metrics: {}", exc)
            return False

    def get_agent_creation_history(self, agent_name: str | None = None) -> list[dict[str, Any]]:
        """Retrieve agent creation history from memory.

        Args:
            agent_name: Optional agent name to filter by. If None, returns all.

        Returns:
            List of creation event dictionaries.
        """
        try:
            events = self.memory_service.get_dynamic_agent_events("agent_creation")

            if agent_name:
                events = [e for e in events if e.get("agent_name") == agent_name]

            return events

        except Exception as exc:
            logger.error("Failed to retrieve agent creation history: {}", exc)
            return []

    def get_agent_usage_history(self, agent_name: str | None = None) -> list[dict[str, Any]]:
        """Retrieve agent usage history from memory.

        Args:
            agent_name: Optional agent name to filter by. If None, returns all.

        Returns:
            List of usage event dictionaries.
        """
        try:
            events = self.memory_service.get_dynamic_agent_events("agent_usage")

            if agent_name:
                events = [e for e in events if e.get("agent_name") == agent_name]

            return events

        except Exception as exc:
            logger.error("Failed to retrieve agent usage history: {}", exc)
            return []

    def get_agent_success_metrics(self, agent_name: str) -> dict[str, Any] | None:
        """Retrieve success metrics for a specific agent.

        Args:
            agent_name: Name of the agent.

        Returns:
            Dictionary with success metrics or None if not found.
        """
        try:
            events = self.memory_service.get_dynamic_agent_events("agent_success_metrics")
            agent_events = [e for e in events if e.get("agent_name") == agent_name]

            if not agent_events:
                return None

            # Get the most recent metrics
            latest_event = max(agent_events, key=lambda e: e.get("timestamp", ""))

            return latest_event

        except Exception as exc:
            logger.error("Failed to retrieve agent success metrics: {}", exc)
            return None

    def calculate_agent_performance(self, agent_name: str) -> dict[str, Any]:
        """Calculate overall performance metrics for an agent.

        Args:
            agent_name: Name of the agent.

        Returns:
            Dictionary with performance metrics.
        """
        try:
            usage_events = self.get_agent_usage_history(agent_name)
            success_events = self.memory_service.get_dynamic_agent_events("agent_success_metrics")
            agent_success_events = [e for e in success_events if e.get("agent_name") == agent_name]

            total_usage = len(usage_events)
            successful_usage = sum(1 for e in usage_events if e.get("success", False))

            if total_usage > 0:
                success_rate = successful_usage / total_usage
            else:
                success_rate = 0.0

            avg_execution_time = 0.0
            if usage_events:
                execution_times = [e.get("execution_time", 0) for e in usage_events]
                avg_execution_time = sum(execution_times) / len(execution_times)

            latest_success_score = 0.0
            if agent_success_events:
                latest_event = max(agent_success_events, key=lambda e: e.get("timestamp", ""))
                latest_success_score = latest_event.get("success_score", 0.0)

            return {
                "agent_name": agent_name,
                "total_usage": total_usage,
                "successful_usage": successful_usage,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "latest_success_score": latest_success_score,
            }

        except Exception as exc:
            logger.error("Failed to calculate agent performance: {}", exc)
            return {
                "agent_name": agent_name,
                "total_usage": 0,
                "successful_usage": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "latest_success_score": 0.0,
            }
