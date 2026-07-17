"""Utilities for creating and safely updating shared workflow context."""

from __future__ import annotations

from loguru import logger

from superagent.context_models import Finding, Recommendation, Risk, TaskContext


class ContextManager:
    """Create, validate, and update shared task context objects."""

    def create_context(self, query: str, task_type: str, metadata: dict[str, object] | None = None) -> TaskContext:
        context = TaskContext(query=query, task_type=task_type, metadata=dict(metadata or {}))
        logger.info("Context created: query='{}', task_type='{}'", query, task_type)
        return context

    def validate_context(self, context: TaskContext) -> TaskContext:
        validated_context = TaskContext.model_validate(context.model_dump())
        logger.info("Context validated: query='{}', task_type='{}'", validated_context.query, validated_context.task_type)
        return validated_context

    def add_finding(self, context: TaskContext, finding: Finding) -> TaskContext:
        context.findings.append(finding)
        logger.info("Finding added by {}: {}", finding.source_agent, finding.content)
        return context

    def add_risk(self, context: TaskContext, risk: Risk) -> TaskContext:
        context.risks.append(risk)
        logger.info("Risk added by {}: {}", risk.source_agent, risk.description)
        return context

    def add_recommendation(self, context: TaskContext, recommendation: Recommendation) -> TaskContext:
        context.recommendations.append(recommendation)
        logger.info("Recommendation added by {}: {}", recommendation.source_agent, recommendation.content)
        return context

    def add_agent_history(self, context: TaskContext, agent_name: str) -> TaskContext:
        context.agent_history.append(agent_name)
        logger.info("Agent context updated: {}", context.agent_history)
        return context

    def get_summary(self, context: TaskContext) -> dict[str, object]:
        return {
            "query": context.query,
            "task_type": context.task_type,
            "findings": len(context.findings),
            "risks": len(context.risks),
            "recommendations": len(context.recommendations),
            "agent_history": list(context.agent_history),
        }