"""Build Neo4j knowledge graph entries from workflow context."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from loguru import logger

from agents.agent_metadata import get_agent_metadata
from config.settings import get_settings
from graph.graph_manager import GraphManager
from superagent.context_models import TaskContext


class KnowledgeGraphBuilder:
	"""Translate workflow context into nodes and relationships."""

	def __init__(self, graph_manager: GraphManager) -> None:
		self.graph_manager = graph_manager

	def _register_agent(self, agent_name: str) -> None:
		metadata = get_agent_metadata(agent_name)
		description = metadata.description if metadata is not None else "Workflow agent"
		self.graph_manager.create_agent_node(agent_name, description)
		if metadata is None:
			return
		for skill in metadata.skills:
			self.graph_manager.create_skill_node(skill)
			self.graph_manager.create_relationship(
				"Agent",
				{"name": agent_name},
				"AGENT_HAS_SKILL",
				"Skill",
				{"name": skill},
			)

	def build_from_context(self, context: TaskContext) -> dict[str, object]:
		"""Create or update graph nodes for the supplied workflow context."""
		settings = get_settings()
		task_id = str(context.metadata.get("task_id") or uuid4())
		context.metadata["task_id"] = task_id
		timestamp = datetime.now(timezone.utc).isoformat()
		selected_agents = list(dict.fromkeys([*(context.metadata.get("selected_agents") or []), *context.agent_history]))

		self.graph_manager.create_task_node(task_id, context.query, context.task_type, timestamp)

		for agent_name in selected_agents:
			self._register_agent(agent_name)
			self.graph_manager.create_relationship(
				"Task",
				{"task_id": task_id},
				"TASK_USED_AGENT",
				"Agent",
				{"name": agent_name},
			)

		# Enforce node limits for findings
		findings_to_create = context.findings[:settings.max_findings_per_task]
		if len(context.findings) > settings.max_findings_per_task:
			logger.warning(
				"Limiting findings from {} to {} (max limit)",
				len(context.findings),
				settings.max_findings_per_task,
			)

		for finding in findings_to_create:
			self._register_agent(finding.source_agent)
			finding_identity = {
				"task_id": task_id,
				"source_agent": finding.source_agent,
				"content": finding.content,
				"category": finding.category,
				"confidence": finding.confidence,
			}
			self.graph_manager.create_finding_node(
				task_id,
				finding.source_agent,
				finding.content,
				finding.category,
				finding.confidence,
			)
			self.graph_manager.create_relationship("Task", {"task_id": task_id}, "TASK_GENERATED_FINDING", "Finding", finding_identity)
			self.graph_manager.create_relationship(
				"Agent",
				{"name": finding.source_agent},
				"AGENT_CREATED_FINDING",
				"Finding",
				finding_identity,
			)

		# Enforce node limits for risks
		risks_to_create = context.risks[:settings.max_risks_per_task]
		if len(context.risks) > settings.max_risks_per_task:
			logger.warning(
				"Limiting risks from {} to {} (max limit)",
				len(context.risks),
				settings.max_risks_per_task,
			)

		for risk in risks_to_create:
			self._register_agent(risk.source_agent)
			risk_identity = {
				"task_id": task_id,
				"source_agent": risk.source_agent,
				"description": risk.description,
				"severity": risk.severity,
			}
			self.graph_manager.create_risk_node(task_id, risk.source_agent, risk.description, risk.severity)
			self.graph_manager.create_relationship("Task", {"task_id": task_id}, "TASK_GENERATED_RISK", "Risk", risk_identity)
			self.graph_manager.create_relationship(
				"Agent",
				{"name": risk.source_agent},
				"AGENT_CREATED_RISK",
				"Risk",
				risk_identity,
			)

		# Enforce node limits for recommendations
		recommendations_to_create = context.recommendations[:settings.max_recommendations_per_task]
		if len(context.recommendations) > settings.max_recommendations_per_task:
			logger.warning(
				"Limiting recommendations from {} to {} (max limit)",
				len(context.recommendations),
				settings.max_recommendations_per_task,
			)

		for recommendation in recommendations_to_create:
			self._register_agent(recommendation.source_agent)
			recommendation_identity = {
				"task_id": task_id,
				"source_agent": recommendation.source_agent,
				"content": recommendation.content,
				"priority": recommendation.priority,
			}
			self.graph_manager.create_recommendation_node(
				task_id,
				recommendation.source_agent,
				recommendation.content,
				recommendation.priority,
			)
			self.graph_manager.create_relationship(
				"Task",
				{"task_id": task_id},
				"TASK_GENERATED_RECOMMENDATION",
				"Recommendation",
				recommendation_identity,
			)
			self.graph_manager.create_relationship(
				"Agent",
				{"name": recommendation.source_agent},
				"AGENT_CREATED_RECOMMENDATION",
				"Recommendation",
				recommendation_identity,
			)

		summary = {
			"task_id": task_id,
			"agents": len(selected_agents),
			"findings": len(findings_to_create),
			"risks": len(risks_to_create),
			"recommendations": len(recommendations_to_create),
		}
		logger.info("Knowledge graph build complete: {}", summary)
		return summary