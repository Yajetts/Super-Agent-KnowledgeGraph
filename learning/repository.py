"""Repository layer for learning persistence operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from learning.database_models import WorkflowPatternDB, WorkflowReflectionDB
from learning.models import LearningStats, WorkflowPattern
from memory.database import get_db_manager


class LearningRepository:
    """Handle database operations for learning records."""

    def __init__(self) -> None:
        """Initialize repository with database manager."""
        self.db_manager = get_db_manager()

    def save_reflection(
        self,
        workflow_id: int,
        task_type: str,
        workflow_pattern: str,
        agents_used: list[str],
        execution_time: float,
        retrieval_count: int,
        reflection_summary: str,
        success_score: float,
    ) -> int:
        """Save a workflow reflection and return its ID."""
        try:
            with self.db_manager.session_scope() as session:
                reflection = WorkflowReflectionDB(
                    workflow_id=workflow_id,
                    task_type=task_type,
                    workflow_pattern=workflow_pattern,
                    agents_used=json.dumps(agents_used),
                    execution_time=execution_time,
                    retrieval_count=retrieval_count,
                    reflection_summary=reflection_summary,
                    success_score=success_score,
                )
                session.add(reflection)
                session.flush()
                reflection_id = reflection.id
                logger.info("Workflow reflection saved with ID: {}", reflection_id)
                return reflection_id
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, skipping reflection storage")
                return 0
            logger.error("Failed to save workflow reflection: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to save workflow reflection: {}", exc)
            raise

    def get_reflection(self, reflection_id: int) -> WorkflowReflectionDB | None:
        """Retrieve a reflection by ID."""
        try:
            with self.db_manager.session_scope() as session:
                reflection = (
                    session.query(WorkflowReflectionDB)
                    .filter(WorkflowReflectionDB.id == reflection_id)
                    .first()
                )
                return reflection
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning None for reflection")
                return None
            logger.error("Failed to retrieve reflection: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve reflection: {}", exc)
            raise

    def get_reflections_by_task_type(self, task_type: str, limit: int = 50) -> list[WorkflowReflectionDB]:
        """Retrieve reflections for a specific task type."""
        try:
            with self.db_manager.session_scope() as session:
                reflections = (
                    session.query(WorkflowReflectionDB)
                    .filter(WorkflowReflectionDB.task_type == task_type)
                    .order_by(WorkflowReflectionDB.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                return reflections
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning empty list for task type reflections")
                return []
            logger.error("Failed to retrieve reflections by task type: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve reflections by task type: {}", exc)
            raise

    def get_recent_reflections(self, limit: int = 20) -> list[WorkflowReflectionDB]:
        """Retrieve recent reflection records."""
        try:
            with self.db_manager.session_scope() as session:
                reflections = (
                    session.query(WorkflowReflectionDB)
                    .order_by(WorkflowReflectionDB.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                return reflections
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning empty list for recent reflections")
                return []
            logger.error("Failed to retrieve recent reflections: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve recent reflections: {}", exc)
            raise

    def save_pattern(
        self,
        task_type: str,
        workflow_pattern: list[str],
        success_score: float,
        usage_count: int = 1,
    ) -> int:
        """Save or update a workflow pattern and return its ID."""
        try:
            with self.db_manager.session_scope() as session:
                # Check if pattern already exists for this task type
                existing_pattern = (
                    session.query(WorkflowPatternDB)
                    .filter(WorkflowPatternDB.task_type == task_type)
                    .first()
                )

                if existing_pattern:
                    # Update existing pattern
                    existing_pattern.workflow_pattern = json.dumps(workflow_pattern)
                    # Weighted average of success scores
                    existing_pattern.success_score = (
                        (existing_pattern.success_score * existing_pattern.usage_count + success_score)
                        / (existing_pattern.usage_count + 1)
                    )
                    existing_pattern.usage_count += 1
                    existing_pattern.last_updated = datetime.utcnow()
                    session.flush()
                    pattern_id = existing_pattern.id
                    logger.info("Workflow pattern updated for task type: {} with ID: {}", task_type, pattern_id)
                else:
                    # Create new pattern
                    pattern = WorkflowPatternDB(
                        task_type=task_type,
                        workflow_pattern=json.dumps(workflow_pattern),
                        success_score=success_score,
                        usage_count=usage_count,
                    )
                    session.add(pattern)
                    session.flush()
                    pattern_id = pattern.id
                    logger.info("Workflow pattern saved for task type: {} with ID: {}", task_type, pattern_id)

                return pattern_id
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, skipping pattern storage")
                return 0
            logger.error("Failed to save workflow pattern: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to save workflow pattern: {}", exc)
            raise

    def get_pattern(self, task_type: str) -> dict[str, Any] | None:
        """Retrieve a pattern by task type."""
        try:
            with self.db_manager.session_scope() as session:
                pattern = (
                    session.query(WorkflowPatternDB)
                    .filter(WorkflowPatternDB.task_type == task_type)
                    .first()
                )
                if pattern:
                    # Convert to dictionary while still in session scope
                    pattern_dict = {
                        "id": pattern.id,
                        "task_type": pattern.task_type,
                        "workflow_pattern": pattern.workflow_pattern,
                        "success_score": pattern.success_score,
                        "usage_count": pattern.usage_count,
                        "last_updated": pattern.last_updated,
                    }
                    return pattern_dict
                return None
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning None for pattern")
                return None
            logger.error("Failed to retrieve pattern: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve pattern: {}", exc)
            raise

    def get_all_patterns(self) -> list[dict[str, Any]]:
        """Retrieve all workflow patterns."""
        try:
            with self.db_manager.session_scope() as session:
                patterns = session.query(WorkflowPatternDB).order_by(WorkflowPatternDB.success_score.desc()).all()
                # Convert to dictionaries while still in session scope
                pattern_dicts = []
                for pattern in patterns:
                    pattern_dict = {
                        "id": pattern.id,
                        "task_type": pattern.task_type,
                        "workflow_pattern": pattern.workflow_pattern,  # Keep as JSON string
                        "success_score": pattern.success_score,
                        "usage_count": pattern.usage_count,
                        "last_updated": pattern.last_updated,
                    }
                    pattern_dicts.append(pattern_dict)
                return pattern_dicts
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning empty list for patterns")
                return []
            logger.error("Failed to retrieve all patterns: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve all patterns: {}", exc)
            raise

    def get_successful_patterns(self, min_success_score: float = 0.7) -> list[dict[str, Any]]:
        """Retrieve patterns with success score above threshold."""
        try:
            with self.db_manager.session_scope() as session:
                patterns = (
                    session.query(WorkflowPatternDB)
                    .filter(WorkflowPatternDB.success_score >= min_success_score)
                    .order_by(WorkflowPatternDB.success_score.desc())
                    .all()
                )
                # Convert to dictionaries while still in session scope
                pattern_dicts = []
                for pattern in patterns:
                    pattern_dict = {
                        "id": pattern.id,
                        "task_type": pattern.task_type,
                        "workflow_pattern": pattern.workflow_pattern,
                        "success_score": pattern.success_score,
                        "usage_count": pattern.usage_count,
                        "last_updated": pattern.last_updated,
                    }
                    pattern_dicts.append(pattern_dict)
                return pattern_dicts
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning empty list for successful patterns")
                return []
            logger.error("Failed to retrieve successful patterns: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to retrieve successful patterns: {}", exc)
            raise

    def get_reflection_count(self) -> int:
        """Get total number of reflections."""
        try:
            with self.db_manager.session_scope() as session:
                count = session.query(WorkflowReflectionDB).count()
                return count
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning 0 for reflection count")
                return 0
            logger.error("Failed to get reflection count: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get reflection count: {}", exc)
            raise

    def get_pattern_count(self) -> int:
        """Get total number of patterns."""
        try:
            with self.db_manager.session_scope() as session:
                count = session.query(WorkflowPatternDB).count()
                return count
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning 0 for pattern count")
                return 0
            logger.error("Failed to get pattern count: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get pattern count: {}", exc)
            raise

    def get_successful_pattern_count(self, min_success_score: float = 0.7) -> int:
        """Get number of patterns with success score above threshold."""
        try:
            with self.db_manager.session_scope() as session:
                count = (
                    session.query(WorkflowPatternDB)
                    .filter(WorkflowPatternDB.success_score >= min_success_score)
                    .count()
                )
                return count
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning 0 for successful pattern count")
                return 0
            logger.error("Failed to get successful pattern count: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get successful pattern count: {}", exc)
            raise

    def get_average_success_score(self) -> float:
        """Get average success score across all patterns."""
        try:
            with self.db_manager.session_scope() as session:
                from sqlalchemy import func

                avg_score = session.query(func.avg(WorkflowPatternDB.success_score)).scalar()
                return float(avg_score) if avg_score is not None else 0.0
        except RuntimeError as exc:
            if "Database connection unavailable" in str(exc):
                logger.warning("Learning layer unavailable, returning 0.0 for average success score")
                return 0.0
            logger.error("Failed to get average success score: {}", exc)
            raise
        except Exception as exc:
            logger.error("Failed to get average success score: {}", exc)
            raise

    def get_learning_stats(self) -> LearningStats:
        """Get comprehensive learning system statistics."""
        try:
            reflection_count = self.get_reflection_count()
            pattern_count = self.get_pattern_count()
            successful_pattern_count = self.get_successful_pattern_count()
            avg_success_score = self.get_average_success_score()

            return LearningStats(
                reflections=reflection_count,
                patterns=pattern_count,
                successful_patterns=successful_pattern_count,
                avg_success_score=avg_success_score,
            )
        except Exception as exc:
            logger.error("Failed to get learning stats: {}", exc)
            raise
