"""Reflection engine for analyzing completed workflows."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from learning.models import WorkflowReflection
from learning.repository import LearningRepository
from learning.scoring import calculate_success_score_from_workflow
from memory.models import WorkflowMemory


class ReflectionEngine:
    """Analyze completed workflows and generate reflections."""

    def __init__(self, repository: LearningRepository | None = None) -> None:
        """Initialize reflection engine with repository."""
        self.repository = repository or LearningRepository()

    def reflect_on_workflow(self, workflow: WorkflowMemory) -> WorkflowReflection | None:
        """
        Analyze a completed workflow and generate a reflection.

        Args:
            workflow: The workflow memory record to analyze

        Returns:
            WorkflowReflection if successful, None otherwise
        """
        try:
            logger.info("Starting reflection on workflow ID: {}", workflow.id)

            # Extract workflow data
            workflow_data = {
                "execution_completed": True,
                "response_generated": True,
                "graph_results_count": workflow.graph_results_count,
                "vector_results_count": workflow.vector_results_count,
                "fusion_results_count": workflow.fusion_results_count,
                "execution_time": workflow.execution_time,
                "has_critical_errors": False,
            }

            # Calculate success score
            success_score = calculate_success_score_from_workflow(workflow_data)
            logger.info("Success score calculated for workflow {}: {}", workflow.id, success_score)

            # Generate reflection summary
            reflection_summary = self._generate_reflection_summary(
                task_type=workflow.task_type,
                agents_used=json.loads(workflow.agents_used),
                success_score=success_score,
                execution_time=workflow.execution_time,
                retrieval_count=workflow.graph_results_count + workflow.vector_results_count + workflow.fusion_results_count,
            )

            # Create workflow pattern string
            agents_used = json.loads(workflow.agents_used)
            workflow_pattern = " → ".join(agents_used)

            # Calculate total retrieval count
            retrieval_count = workflow.graph_results_count + workflow.vector_results_count + workflow.fusion_results_count

            # Create reflection object
            reflection = WorkflowReflection(
                workflow_id=workflow.id,
                task_type=workflow.task_type,
                workflow_pattern=workflow_pattern,
                agents_used=agents_used,
                execution_time=workflow.execution_time,
                retrieval_count=retrieval_count,
                reflection_summary=reflection_summary,
                success_score=success_score,
                timestamp=workflow.timestamp,
            )

            # Store reflection
            reflection_id = self.repository.save_reflection(
                workflow_id=workflow.id,
                task_type=workflow.task_type,
                workflow_pattern=workflow_pattern,
                agents_used=agents_used,
                execution_time=workflow.execution_time,
                retrieval_count=retrieval_count,
                reflection_summary=reflection_summary,
                success_score=success_score,
            )

            if reflection_id > 0:
                logger.info("Reflection stored successfully with ID: {}", reflection_id)
            else:
                logger.warning("Reflection storage failed or was skipped")

            return reflection

        except Exception as exc:
            logger.error("Failed to reflect on workflow {}: {}", workflow.id, exc)
            return None

    def _generate_reflection_summary(
        self,
        task_type: str,
        agents_used: list[str],
        success_score: float,
        execution_time: float,
        retrieval_count: int,
    ) -> str:
        """
        Generate a human-readable reflection summary.

        Args:
            task_type: The type of task executed
            agents_used: List of agents used in order
            success_score: Calculated success score
            execution_time: Total execution time
            retrieval_count: Total retrieval operations

        Returns:
            A reflection summary string
        """
        # Build agent sequence description
        agent_sequence = " → ".join(agents_used)

        # Determine success level
        if success_score >= 0.9:
            success_level = "excellent"
        elif success_score >= 0.7:
            success_level = "good"
        elif success_score >= 0.5:
            success_level = "moderate"
        else:
            success_level = "poor"

        # Generate summary
        summary_parts = [
            f"{task_type.replace('_', ' ').title()} workflows",
            f"involving {agent_sequence}",
            f"achieved {success_level} performance",
        ]

        if retrieval_count > 0:
            summary_parts.append(f"with {retrieval_count} retrieval operations")

        if execution_time < 10:
            summary_parts.append("and executed quickly")
        elif execution_time < 30:
            summary_parts.append("with reasonable execution time")
        else:
            summary_parts.append("but took longer to execute")

        if success_score >= 0.7:
            summary_parts.append("Pattern appears effective.")

        return " ".join(summary_parts)

    def generate_reflection(self, workflow_data: dict[str, Any]) -> str:
        """
        Generate a reflection summary from workflow data.

        Args:
            workflow_data: Dictionary containing workflow execution data

        Returns:
            A reflection summary string
        """
        task_type = workflow_data.get("task_type", "unknown")
        agents_used = workflow_data.get("agents_used", [])
        success_score = workflow_data.get("success_score", 0.0)
        execution_time = workflow_data.get("execution_time", 0.0)
        retrieval_count = workflow_data.get("retrieval_count", 0)

        return self._generate_reflection_summary(
            task_type=task_type,
            agents_used=agents_used,
            success_score=success_score,
            execution_time=execution_time,
            retrieval_count=retrieval_count,
        )

    def store_reflection(self, reflection: WorkflowReflection) -> int:
        """
        Store a reflection in the repository.

        Args:
            reflection: The reflection to store

        Returns:
            The ID of the stored reflection, or 0 if storage failed
        """
        try:
            reflection_id = self.repository.save_reflection(
                workflow_id=reflection.workflow_id,
                task_type=reflection.task_type,
                workflow_pattern=reflection.workflow_pattern,
                agents_used=reflection.agents_used,
                execution_time=reflection.execution_time,
                retrieval_count=reflection.retrieval_count,
                reflection_summary=reflection.reflection_summary,
                success_score=reflection.success_score,
            )
            logger.info("Reflection stored with ID: {}", reflection_id)
            return reflection_id
        except Exception as exc:
            logger.error("Failed to store reflection: {}", exc)
            return 0
