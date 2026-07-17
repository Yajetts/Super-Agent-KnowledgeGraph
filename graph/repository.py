"""Cypher query layer for SuperAgent knowledge graph persistence."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
	from graph.graph_manager import GraphManager


class GraphRepository:
	"""Encapsulate graph business logic and Cypher statements."""

	def __init__(self, graph_manager: GraphManager) -> None:
		self.graph_manager = graph_manager

	def _build_properties_clause(self, properties: dict[str, Any], prefix: str = "") -> tuple[str, dict[str, Any]]:
		parts: list[str] = []
		parameters: dict[str, Any] = {}
		for key, value in properties.items():
			parameter_name = f"{prefix}{key}"
			parts.append(f"{key}: ${parameter_name}")
			parameters[parameter_name] = value
		return ", ".join(parts), parameters

	def _merge_node(self, label: str, match_properties: dict[str, Any], set_properties: dict[str, Any] | None = None) -> list[dict[str, Any]]:
		set_properties = dict(set_properties or {})
		match_clause, match_parameters = self._build_properties_clause(match_properties)
		query = f"MERGE (node:{label} {{{match_clause}}})"
		parameters = dict(match_parameters)
		if set_properties:
			set_clause = ", ".join(f"node.{key} = ${key}" for key in set_properties)
			query = f"{query} SET {set_clause}"
			parameters.update(set_properties)
		query = f"{query} RETURN node"
		#logger.info("Graph node write prepared for label {}", label)
		return self.graph_manager.run_write(query, parameters)

	def _match_exists(self, query: str, parameters: dict[str, Any]) -> bool:
		records = self.graph_manager.run_read(query, parameters)
		if not records:
			return False
		return bool(records[0].get("exists", False))

	def create_task_node(self, task_id: str, query_text: str, task_type: str, timestamp: str) -> list[dict[str, Any]]:
		return self._merge_node(
			"Task",
			{"task_id": task_id},
			{"query": query_text, "task_type": task_type, "timestamp": timestamp},
		)

	def create_agent_node(self, name: str, description: str) -> list[dict[str, Any]]:
		return self._merge_node("Agent", {"name": name}, {"description": description})

	def create_finding_node(
		self,
		task_id: str,
		source_agent: str,
		content: str,
		category: str,
		confidence: float,
	) -> list[dict[str, Any]]:
		return self._merge_node(
			"Finding",
			{
				"task_id": task_id,
				"source_agent": source_agent,
				"content": content,
				"category": category,
				"confidence": confidence,
			},
		)

	def create_risk_node(
		self,
		task_id: str,
		source_agent: str,
		description: str,
		severity: str,
	) -> list[dict[str, Any]]:
		return self._merge_node(
			"Risk",
			{"task_id": task_id, "source_agent": source_agent, "description": description, "severity": severity},
		)

	def create_recommendation_node(
		self,
		task_id: str,
		source_agent: str,
		content: str,
		priority: str,
	) -> list[dict[str, Any]]:
		return self._merge_node(
			"Recommendation",
			{"task_id": task_id, "source_agent": source_agent, "content": content, "priority": priority},
		)

	def create_skill_node(self, name: str) -> list[dict[str, Any]]:
		return self._merge_node("Skill", {"name": name})

	def create_relationship(
		self,
		source_label: str,
		source_properties: dict[str, Any],
		relation_type: str,
		target_label: str,
		target_properties: dict[str, Any],
		relationship_properties: dict[str, Any] | None = None,
	) -> list[dict[str, Any]]:
		relationship_properties = dict(relationship_properties or {})
		source_clause, source_parameters = self._build_properties_clause(source_properties, prefix="source_")
		target_clause, target_parameters = self._build_properties_clause(target_properties, prefix="target_")
		query = (
			f"MATCH (source:{source_label} {{{source_clause}}}), "
			f"(target:{target_label} {{{target_clause}}}) "
			f"MERGE (source)-[relationship:{relation_type}]->(target)"
		)
		parameters = {**source_parameters, **target_parameters}
		if relationship_properties:
			set_clause = ", ".join(f"relationship.{key} = ${key}" for key in relationship_properties)
			query = f"{query} SET {set_clause}"
			parameters.update(relationship_properties)
		query = f"{query} RETURN relationship"
		#logger.info("Graph relationship write prepared: {}", relation_type)
		return self.graph_manager.run_write(query, parameters)

	def graph_exists(self) -> bool:
		query = "MATCH (node) RETURN count(node) > 0 AS exists"
		return self._match_exists(query, {})

	def node_exists(self, label: str, properties: dict[str, Any]) -> bool:
		match_clause, parameters = self._build_properties_clause(properties)
		query = f"MATCH (node:{label} {{{match_clause}}}) RETURN count(node) > 0 AS exists"
		return self._match_exists(query, parameters)

	def relationship_exists(
		self,
		relation_type: str,
		source_label: str,
		source_properties: dict[str, Any],
		target_label: str,
		target_properties: dict[str, Any],
	) -> bool:
		source_clause, source_parameters = self._build_properties_clause(source_properties, prefix="source_")
		target_clause, target_parameters = self._build_properties_clause(target_properties, prefix="target_")
		query = (
			f"MATCH (source:{source_label} {{{source_clause}}})-[:{relation_type}]->(target:{target_label} {{{target_clause}}}) "
			"RETURN count(*) > 0 AS exists"
		)
		return self._match_exists(query, {**source_parameters, **target_parameters})

	def get_stats(self) -> dict[str, int]:
		query = (
			"MATCH (task:Task) "
			"OPTIONAL MATCH (agent:Agent) "
			"OPTIONAL MATCH (finding:Finding) "
			"OPTIONAL MATCH (risk:Risk) "
			"OPTIONAL MATCH (recommendation:Recommendation) "
			"RETURN count(DISTINCT task) AS tasks, "
			"count(DISTINCT agent) AS agents, "
			"count(DISTINCT finding) AS findings, "
			"count(DISTINCT risk) AS risks, "
			"count(DISTINCT recommendation) AS recommendations"
		)
		records = self.graph_manager.run_read(query)
		if not records:
			return {"tasks": 0, "agents": 0, "findings": 0, "risks": 0, "recommendations": 0}
		record = records[0]
		return {
			"tasks": int(record.get("tasks", 0)),
			"agents": int(record.get("agents", 0)),
			"findings": int(record.get("findings", 0)),
			"risks": int(record.get("risks", 0)),
			"recommendations": int(record.get("recommendations", 0)),
		}

	def get_schema_summary(self) -> dict[str, object]:
		return {
			"node_types": [
				{"label": "Task", "properties": ["task_id", "query", "task_type", "timestamp"]},
				{"label": "Agent", "properties": ["name", "description"]},
				{"label": "Finding", "properties": ["task_id", "source_agent", "content", "category", "confidence"]},
				{"label": "Risk", "properties": ["task_id", "source_agent", "description", "severity"]},
				{"label": "Recommendation", "properties": ["task_id", "source_agent", "content", "priority"]},
				{"label": "Skill", "properties": ["name"]},
			],
			"relationship_types": [
				{"type": "TASK_GENERATED_FINDING", "source": "Task", "target": "Finding"},
				{"type": "TASK_GENERATED_RISK", "source": "Task", "target": "Risk"},
				{"type": "TASK_GENERATED_RECOMMENDATION", "source": "Task", "target": "Recommendation"},
				{"type": "AGENT_CREATED_FINDING", "source": "Agent", "target": "Finding"},
				{"type": "AGENT_CREATED_RISK", "source": "Agent", "target": "Risk"},
				{"type": "AGENT_CREATED_RECOMMENDATION", "source": "Agent", "target": "Recommendation"},
				{"type": "AGENT_HAS_SKILL", "source": "Agent", "target": "Skill"},
				{"type": "TASK_USED_AGENT", "source": "Task", "target": "Agent"},
			],
		}