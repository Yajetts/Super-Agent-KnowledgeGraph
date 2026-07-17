"""Query engine for memory analytics and statistics."""

from __future__ import annotations

from typing import Any

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from memory.database import get_db_manager
from memory.models import AgentExecutionMemory, WorkflowMemory


class MemoryQueryEngine:
    """Query engine for memory analytics."""

    def __init__(self) -> None:
        """Initialize query engine with database manager."""
        self.db_manager = get_db_manager()

    def get_recent_workflows(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent workflows with details."""
        try:
            import json

            with self.db_manager.session_scope() as session:
                workflows = (
                    session.query(WorkflowMemory)
                    .order_by(WorkflowMemory.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                result = []
                for workflow in workflows:
                    result.append(
                        {
                            "id": workflow.id,
                            "query": workflow.query,
                            "task_type": workflow.task_type,
                            "timestamp": workflow.timestamp.isoformat(),
                            "execution_time": workflow.execution_time,
                            "agents_used": json.loads(workflow.agents_used),
                            "graph_results_count": workflow.graph_results_count,
                            "vector_results_count": workflow.vector_results_count,
                            "fusion_results_count": workflow.fusion_results_count,
                        }
                    )
                logger.info("Retrieved {} recent workflows", len(result))
                return result
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning empty list for recent workflows")
                return []
            logger.error("Failed to get recent workflows: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get recent workflows: {}", exc)
            raise

    def get_most_used_agents(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most frequently used agents."""
        try:
            with self.db_manager.session_scope() as session:
                agent_counts = (
                    session.query(
                        AgentExecutionMemory.agent_name,
                        func.count(AgentExecutionMemory.id).label("count"),
                    )
                    .group_by(AgentExecutionMemory.agent_name)
                    .order_by(func.count(AgentExecutionMemory.id).desc())
                    .limit(limit)
                    .all()
                )
                result = [{"agent_name": name, "usage_count": count} for name, count in agent_counts]
                logger.info("Retrieved most used agents: {}", result)
                return result
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning empty list for most used agents")
                return []
            logger.error("Failed to get most used agents: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get most used agents: {}", exc)
            raise

    def get_average_execution_time(self, agent_name: str | None = None) -> float:
        """Get average execution time, optionally filtered by agent."""
        try:
            with self.db_manager.session_scope() as session:
                if agent_name:
                    avg_time = (
                        session.query(func.avg(AgentExecutionMemory.execution_time))
                        .filter(AgentExecutionMemory.agent_name == agent_name)
                        .scalar()
                    )
                else:
                    avg_time = session.query(func.avg(WorkflowMemory.execution_time)).scalar()
                
                result = float(avg_time) if avg_time else 0.0
                logger.info("Average execution time for {}: {}", agent_name or "all workflows", result)
                return result
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning 0.0 for average execution time")
                return 0.0
            logger.error("Failed to get average execution time: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get average execution time: {}", exc)
            raise

    def get_workflow_statistics(self) -> dict[str, Any]:
        """Get comprehensive workflow statistics."""
        try:
            import json

            with self.db_manager.session_scope() as session:
                total_workflows = session.query(WorkflowMemory).count()
                total_agent_executions = session.query(AgentExecutionMemory).count()
                
                avg_workflow_time = session.query(func.avg(WorkflowMemory.execution_time)).scalar() or 0.0
                avg_agent_time = session.query(func.avg(AgentExecutionMemory.execution_time)).scalar() or 0.0
                
                # Task type distribution
                task_type_counts = (
                    session.query(
                        WorkflowMemory.task_type,
                        func.count(WorkflowMemory.id).label("count"),
                    )
                    .group_by(WorkflowMemory.task_type)
                    .all()
                )
                task_distribution = {task_type: count for task_type, count in task_type_counts}
                
                # Agent usage distribution
                agent_counts = (
                    session.query(
                        AgentExecutionMemory.agent_name,
                        func.count(AgentExecutionMemory.id).label("count"),
                    )
                    .group_by(AgentExecutionMemory.agent_name)
                    .all()
                )
                agent_distribution = {agent_name: count for agent_name, count in agent_counts}
                
                result = {
                    "total_workflows": total_workflows,
                    "total_agent_executions": total_agent_executions,
                    "average_workflow_execution_time": float(avg_workflow_time),
                    "average_agent_execution_time": float(avg_agent_time),
                    "task_type_distribution": task_distribution,
                    "agent_usage_distribution": agent_distribution,
                }
                logger.info("Workflow statistics retrieved: {}", result)
                return result
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning empty statistics")
                return {
                    "total_workflows": 0,
                    "total_agent_executions": 0,
                    "average_workflow_execution_time": 0.0,
                    "average_agent_execution_time": 0.0,
                    "task_type_distribution": {},
                    "agent_usage_distribution": {},
                }
            logger.error("Failed to get workflow statistics: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get workflow statistics: {}", exc)
            raise

    def get_agent_usage_statistics(self) -> list[dict[str, Any]]:
        """Get detailed agent usage statistics."""
        try:
            with self.db_manager.session_scope() as session:
                agent_stats = (
                    session.query(
                        AgentExecutionMemory.agent_name,
                        func.count(AgentExecutionMemory.id).label("total_executions"),
                        func.avg(AgentExecutionMemory.execution_time).label("avg_execution_time"),
                        func.min(AgentExecutionMemory.execution_time).label("min_execution_time"),
                        func.max(AgentExecutionMemory.execution_time).label("max_execution_time"),
                    )
                    .group_by(AgentExecutionMemory.agent_name)
                    .order_by(func.count(AgentExecutionMemory.id).desc())
                    .all()
                )
                
                result = [
                    {
                        "agent_name": name,
                        "total_executions": total,
                        "average_execution_time": float(avg) if avg else 0.0,
                        "min_execution_time": float(min_time) if min_time else 0.0,
                        "max_execution_time": float(max_time) if max_time else 0.0,
                    }
                    for name, total, avg, min_time, max_time in agent_stats
                ]
                logger.info("Agent usage statistics retrieved")
                return result
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Memory layer unavailable, returning empty list for agent usage statistics")
                return []
            logger.error("Failed to get agent usage statistics: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get agent usage statistics: {}", exc)
            raise


# Global query engine instance
_query_engine: MemoryQueryEngine | None = None


def get_memory_query_engine() -> MemoryQueryEngine:
    """Get or create the global query engine instance."""
    global _query_engine
    if _query_engine is None:
        _query_engine = MemoryQueryEngine()
    return _query_engine
