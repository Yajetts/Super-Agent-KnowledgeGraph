"""Success scoring for workflow execution evaluation."""

from __future__ import annotations

from typing import Any

from loguru import logger


def calculate_success_score(
    execution_completed: bool,
    response_generated: bool,
    retrieval_context_available: bool,
    execution_time: float,
    has_critical_errors: bool,
    max_execution_time: float = 300.0,
) -> float:
    """
    Calculate a success score for a workflow execution using heuristics.

    Args:
        execution_completed: Whether the workflow completed without crashing
        response_generated: Whether a response was successfully generated
        retrieval_context_available: Whether retrieval context was available
        execution_time: Total execution time in seconds
        has_critical_errors: Whether critical errors occurred during execution
        max_execution_time: Maximum acceptable execution time (default: 5 minutes)

    Returns:
        Success score between 0.0 and 1.0
    """
    score = 0.0

    # Base score for completion
    if execution_completed:
        score += 0.3
        logger.debug("Workflow completed successfully: +0.3 to score")
    else:
        logger.warning("Workflow did not complete: no base score")

    # Response generation
    if response_generated:
        score += 0.3
        logger.debug("Response generated: +0.3 to score")
    else:
        logger.warning("No response generated: missing 0.3 points")

    # Retrieval context availability
    if retrieval_context_available:
        score += 0.2
        logger.debug("Retrieval context available: +0.2 to score")
    else:
        logger.warning("No retrieval context available: missing 0.2 points")

    # Execution time penalty (if too long)
    if execution_time <= max_execution_time:
        time_score = 0.2
    else:
        # Linear penalty for exceeding max time
        time_penalty = min((execution_time - max_execution_time) / max_execution_time, 1.0)
        time_score = 0.2 * (1.0 - time_penalty)
        logger.debug(
            "Execution time exceeded threshold: {}s vs {}s max, time score: {}",
            execution_time,
            max_execution_time,
            time_score,
        )
    score += time_score

    # Critical errors penalty
    if has_critical_errors:
        score = max(0.0, score - 0.5)
        logger.warning("Critical errors detected: -0.5 penalty")

    # Ensure score is within bounds
    final_score = max(0.0, min(1.0, score))
    logger.info("Final success score calculated: {}", final_score)

    return final_score


def calculate_success_score_from_workflow(
    workflow_data: dict[str, Any],
    max_execution_time: float = 300.0,
) -> float:
    """
    Calculate success score from workflow memory data.

    Args:
        workflow_data: Dictionary containing workflow execution data
        max_execution_time: Maximum acceptable execution time

    Returns:
        Success score between 0.0 and 1.0
    """
    execution_completed = workflow_data.get("execution_completed", True)
    response_generated = workflow_data.get("response_generated", True)
    retrieval_context_available = (
        (workflow_data.get("graph_results_count", 0) > 0)
        or (workflow_data.get("vector_results_count", 0) > 0)
        or (workflow_data.get("fusion_results_count", 0) > 0)
    )
    execution_time = workflow_data.get("execution_time", 0.0)
    has_critical_errors = workflow_data.get("has_critical_errors", False)

    return calculate_success_score(
        execution_completed=execution_completed,
        response_generated=response_generated,
        retrieval_context_available=retrieval_context_available,
        execution_time=execution_time,
        has_critical_errors=has_critical_errors,
        max_execution_time=max_execution_time,
    )
