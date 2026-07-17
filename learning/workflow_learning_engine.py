"""Workflow learning engine for pattern discovery and workflow recommendations."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any

from loguru import logger

from learning.models import WorkflowRecommendation
from learning.reflection_engine import ReflectionEngine
from learning.repository import LearningRepository
from learning.workflow_registry import WorkflowRegistry
from memory.models import WorkflowMemory


class WorkflowLearningEngine:
    """Analyze workflow history and recommend workflow structures."""

    def __init__(
        self,
        repository: LearningRepository | None = None,
        registry: WorkflowRegistry | None = None,
        reflection_engine: ReflectionEngine | None = None,
    ) -> None:
        """Initialize workflow learning engine with dependencies."""
        self.repository = repository or LearningRepository()
        self.registry = registry or WorkflowRegistry(repository)
        self.reflection_engine = reflection_engine or ReflectionEngine(repository)

    def learn_from_history(self, limit: int = 100) -> dict[str, Any]:
        """
        Analyze workflow history to discover patterns.

        Args:
            limit: Maximum number of recent workflows to analyze

        Returns:
            Dictionary containing learning results
        """
        try:
            logger.info("Starting learning from workflow history (limit: {})", limit)

            # Get recent reflections
            reflections = self.repository.get_recent_reflections(limit)

            if not reflections:
                logger.info("No reflections found for learning")
                return {"patterns_discovered": 0, "patterns_updated": 0}

            patterns_discovered = 0
            patterns_updated = 0

            # Group reflections by task type
            task_type_groups: dict[str, list[Any]] = defaultdict(list)
            for reflection in reflections:
                task_type_groups[reflection.task_type].append(reflection)

            # Analyze each task type group
            for task_type, group_reflections in task_type_groups.items():
                # Identify most common agent sequence
                agent_sequences = []
                for ref in group_reflections:
                    agents = json.loads(ref.agents_used)
                    agent_sequences.append(tuple(agents))

                # Count frequency of each sequence
                sequence_counter = Counter(agent_sequences)
                if not sequence_counter:
                    continue

                # Get most common sequence
                most_common_sequence, frequency = sequence_counter.most_common(1)[0]

                # Calculate average success score for this sequence
                sequence_reflections = [
                    ref
                    for ref in group_reflections
                    if tuple(json.loads(ref.agents_used)) == most_common_sequence
                ]
                avg_success_score = sum(ref.success_score for ref in sequence_reflections) / len(
                    sequence_reflections
                )

                # Check if pattern already exists
                existing_pattern = self.registry.find_best_pattern(task_type)

                if existing_pattern:
                    # Update existing pattern
                    self.registry.update_pattern_score(task_type, avg_success_score)
                    patterns_updated += 1
                    logger.info(
                        "Updated pattern for task type: {} with new success score: {}",
                        task_type,
                        avg_success_score,
                    )
                else:
                    # Register new pattern if success score is acceptable
                    if avg_success_score >= 0.5:
                        self.registry.register_pattern(
                            task_type=task_type,
                            workflow_pattern=list(most_common_sequence),
                            success_score=avg_success_score,
                            usage_count=frequency,
                        )
                        patterns_discovered += 1
                        logger.info(
                            "Discovered new pattern for task type: {} with success score: {}",
                            task_type,
                            avg_success_score,
                        )

            results = {
                "patterns_discovered": patterns_discovered,
                "patterns_updated": patterns_updated,
                "task_types_analyzed": len(task_type_groups),
            }

            logger.info("Learning from history completed: {}", results)
            return results

        except Exception as exc:
            logger.error("Failed to learn from history: {}", exc)
            return {"patterns_discovered": 0, "patterns_updated": 0, "error": str(exc)}

    def identify_successful_patterns(self, min_success_score: float = 0.7) -> list[dict[str, Any]]:
        """
        Identify patterns with high success scores.

        Args:
            min_success_score: Minimum success score threshold

        Returns:
            List of successful pattern dictionaries
        """
        try:
            patterns = self.registry.get_successful_patterns(min_success_score)
            successful_patterns = []
            for pattern in patterns:
                pattern_dict = {
                    "task_type": pattern.task_type,
                    "workflow_pattern": pattern.workflow_pattern,
                    "success_score": pattern.success_score,
                    "usage_count": pattern.usage_count,
                    "last_updated": pattern.last_updated.isoformat(),
                }
                successful_patterns.append(pattern_dict)

            logger.info(
                "Identified {} successful patterns (score >= {})",
                len(successful_patterns),
                min_success_score,
            )
            return successful_patterns
        except Exception as exc:
            logger.error("Failed to identify successful patterns: {}", exc)
            return []

    def recommend_workflow(self, task_type: str) -> WorkflowRecommendation | None:
        """
        Recommend a workflow structure for a given task type.

        Args:
            task_type: The type of task to recommend a workflow for

        Returns:
            WorkflowRecommendation if a pattern exists, None otherwise
        """
        try:
            logger.info("Generating workflow recommendation for task type: {}", task_type)

            # Find best pattern for task type
            pattern = self.registry.find_best_pattern(task_type)

            if not pattern:
                logger.info("No pattern found for task type: {}", task_type)
                return None

            # Get supporting examples (reflections with this pattern)
            reflections = self.repository.get_reflections_by_task_type(task_type, limit=50)
            supporting_examples = len(
                [r for r in reflections if tuple(json.loads(r.agents_used)) == tuple(pattern.workflow_pattern)]
            )

            # Calculate confidence based on success score and usage count
            confidence = pattern.success_score * min(1.0, pattern.usage_count / 10.0)

            recommendation = WorkflowRecommendation(
                task_type=task_type,
                recommended_agents=pattern.workflow_pattern,
                confidence=confidence,
                supporting_examples=supporting_examples,
            )

            logger.info(
                "Workflow recommendation generated for task type: {} with confidence: {}",
                task_type,
                confidence,
            )
            return recommendation

        except Exception as exc:
            logger.error("Failed to recommend workflow for task type {}: {}", task_type, exc)
            return None

    def update_pattern_scores(self, workflow: WorkflowMemory) -> bool:
        """
        Update pattern scores based on a completed workflow.

        Args:
            workflow: The completed workflow to use for updating

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Generate reflection for the workflow
            reflection = self.reflection_engine.reflect_on_workflow(workflow)

            if not reflection:
                logger.warning("Failed to generate reflection for workflow {}", workflow.id)
                return False

            # Update or register pattern
            existing_pattern = self.registry.find_best_pattern(workflow.task_type)

            if existing_pattern:
                # Update existing pattern with new success score
                success = self.registry.update_pattern_score(workflow.task_type, reflection.success_score)
                logger.info(
                    "Updated pattern score for task type: {} to: {}",
                    workflow.task_type,
                    reflection.success_score,
                )
                return success
            else:
                # Register new pattern if success score is acceptable
                if reflection.success_score >= 0.5:
                    agents_used = json.loads(workflow.agents_used)
                    pattern_id = self.registry.register_pattern(
                        task_type=workflow.task_type,
                        workflow_pattern=agents_used,
                        success_score=reflection.success_score,
                        usage_count=1,
                    )
                    success = pattern_id > 0
                    logger.info(
                        "Registered new pattern for task type: {} with success score: {}",
                        workflow.task_type,
                        reflection.success_score,
                    )
                    return success

            return False

        except Exception as exc:
            logger.error("Failed to update pattern scores for workflow {}: {}", workflow.id, exc)
            return False

    def process_completed_workflow(self, workflow: WorkflowMemory) -> dict[str, Any]:
        """
        Process a completed workflow through the learning pipeline.

        Args:
            workflow: The completed workflow to process

        Returns:
            Dictionary containing processing results
        """
        try:
            logger.info("Processing completed workflow {} through learning pipeline", workflow.id)

            # Generate reflection
            reflection = self.reflection_engine.reflect_on_workflow(workflow)
            reflection_generated = reflection is not None

            # Update pattern scores
            pattern_updated = self.update_pattern_scores(workflow)

            results = {
                "workflow_id": workflow.id,
                "task_type": workflow.task_type,
                "reflection_generated": reflection_generated,
                "pattern_updated": pattern_updated,
                "success_score": reflection.success_score if reflection else 0.0,
            }

            logger.info("Workflow {} processed through learning pipeline: {}", workflow.id, results)
            return results

        except Exception as exc:
            logger.error("Failed to process workflow {} through learning pipeline: {}", workflow.id, exc)
            return {
                "workflow_id": workflow.id,
                "task_type": workflow.task_type,
                "reflection_generated": False,
                "pattern_updated": False,
                "error": str(exc),
            }
