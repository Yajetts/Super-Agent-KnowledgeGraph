"""Workflow pattern registry for storing and retrieving learned patterns."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from learning.database_models import WorkflowPatternDB
from learning.models import WorkflowPattern
from learning.repository import LearningRepository


class WorkflowRegistry:
    """Store and manage reusable workflow patterns."""

    def __init__(self, repository: LearningRepository | None = None) -> None:
        """Initialize workflow registry with repository."""
        self.repository = repository or LearningRepository()

    def register_pattern(
        self,
        task_type: str,
        workflow_pattern: list[str],
        success_score: float,
        usage_count: int = 1,
    ) -> int:
        """
        Register or update a workflow pattern.

        Args:
            task_type: The type of task this pattern applies to
            workflow_pattern: List of agent names in execution order
            success_score: Success score for this pattern
            usage_count: Number of times this pattern has been used

        Returns:
            The ID of the registered pattern, or 0 if registration failed
        """
        try:
            pattern_id = self.repository.save_pattern(
                task_type=task_type,
                workflow_pattern=workflow_pattern,
                success_score=success_score,
                usage_count=usage_count,
            )
            logger.info(
                "Pattern registered for task type: {} with success score: {} and ID: {}",
                task_type,
                success_score,
                pattern_id,
            )
            return pattern_id
        except Exception as exc:
            logger.error("Failed to register pattern for task type {}: {}", task_type, exc)
            return 0

    def get_patterns(self) -> list[WorkflowPattern]:
        """
        Retrieve all registered workflow patterns.

        Returns:
            List of all workflow patterns
        """
        try:
            pattern_dicts = self.repository.get_all_patterns()
            patterns = []
            for pattern_dict in pattern_dicts:
                pattern = WorkflowPattern(
                    id=pattern_dict["id"],
                    task_type=pattern_dict["task_type"],
                    workflow_pattern=json.loads(pattern_dict["workflow_pattern"]),
                    success_score=pattern_dict["success_score"],
                    usage_count=pattern_dict["usage_count"],
                    last_updated=pattern_dict["last_updated"],
                )
                patterns.append(pattern)
            logger.info("Retrieved {} patterns from registry", len(patterns))
            return patterns
        except Exception as exc:
            logger.error("Failed to retrieve patterns: {}", exc)
            return []

    def find_best_pattern(self, task_type: str) -> WorkflowPattern | None:
        """
        Find the best pattern for a given task type.

        Args:
            task_type: The type of task to find a pattern for

        Returns:
            The best pattern for the task type, or None if not found
        """
        try:
            pattern_dict = self.repository.get_pattern(task_type)
            if pattern_dict:
                pattern = WorkflowPattern(
                    id=pattern_dict["id"],
                    task_type=pattern_dict["task_type"],
                    workflow_pattern=json.loads(pattern_dict["workflow_pattern"]),
                    success_score=pattern_dict["success_score"],
                    usage_count=pattern_dict["usage_count"],
                    last_updated=pattern_dict["last_updated"],
                )
                logger.info(
                    "Found pattern for task type: {} with success score: {}",
                    task_type,
                    pattern.success_score,
                )
                return pattern
            logger.info("No pattern found for task type: {}", task_type)
            return None
        except Exception as exc:
            logger.error("Failed to find pattern for task type {}: {}", task_type, exc)
            return None

    def get_pattern_statistics(self) -> dict[str, Any]:
        """
        Get statistics about registered patterns.

        Returns:
            Dictionary containing pattern statistics
        """
        try:
            patterns = self.get_patterns()
            total_patterns = len(patterns)
            successful_patterns = len([p for p in patterns if p.success_score >= 0.7])
            avg_success_score = sum(p.success_score for p in patterns) / total_patterns if total_patterns > 0 else 0.0
            avg_usage_count = sum(p.usage_count for p in patterns) / total_patterns if total_patterns > 0 else 0.0

            # Group by task type
            task_type_counts: dict[str, int] = {}
            for pattern in patterns:
                task_type_counts[pattern.task_type] = task_type_counts.get(pattern.task_type, 0) + 1

            statistics = {
                "total_patterns": total_patterns,
                "successful_patterns": successful_patterns,
                "avg_success_score": avg_success_score,
                "avg_usage_count": avg_usage_count,
                "task_type_distribution": task_type_counts,
            }

            logger.info("Pattern statistics retrieved: {}", statistics)
            return statistics
        except Exception as exc:
            logger.error("Failed to get pattern statistics: {}", exc)
            return {
                "total_patterns": 0,
                "successful_patterns": 0,
                "avg_success_score": 0.0,
                "avg_usage_count": 0.0,
                "task_type_distribution": {},
            }

    def update_pattern_score(self, task_type: str, new_success_score: float) -> bool:
        """
        Update the success score for a pattern.

        Args:
            task_type: The task type of the pattern to update
            new_success_score: The new success score to apply

        Returns:
            True if update was successful, False otherwise
        """
        try:
            pattern = self.find_best_pattern(task_type)
            if pattern:
                # Re-register with updated score (repository handles weighted average)
                pattern_id = self.register_pattern(
                    task_type=task_type,
                    workflow_pattern=pattern.workflow_pattern,
                    success_score=new_success_score,
                    usage_count=pattern.usage_count + 1,
                )
                return pattern_id > 0
            logger.warning("Cannot update score: no pattern found for task type: {}", task_type)
            return False
        except Exception as exc:
            logger.error("Failed to update pattern score for task type {}: {}", task_type, exc)
            return False

    def get_successful_patterns(self, min_success_score: float = 0.7) -> list[WorkflowPattern]:
        """
        Retrieve patterns with success score above threshold.

        Args:
            min_success_score: Minimum success score threshold

        Returns:
            List of successful patterns
        """
        try:
            pattern_dicts = self.repository.get_successful_patterns(min_success_score)
            patterns = []
            for pattern_dict in pattern_dicts:
                pattern = WorkflowPattern(
                    id=pattern_dict["id"],
                    task_type=pattern_dict["task_type"],
                    workflow_pattern=json.loads(pattern_dict["workflow_pattern"]),
                    success_score=pattern_dict["success_score"],
                    usage_count=pattern_dict["usage_count"],
                    last_updated=pattern_dict["last_updated"],
                )
                patterns.append(pattern)
            logger.info(
                "Retrieved {} successful patterns (score >= {})",
                len(patterns),
                min_success_score,
            )
            return patterns
        except Exception as exc:
            logger.error("Failed to retrieve successful patterns: {}", exc)
            return []
