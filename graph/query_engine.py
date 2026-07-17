"""Graph retrieval engine for historical context lookup."""

from __future__ import annotations

import re
from collections import OrderedDict

from loguru import logger

from graph.graph_manager import GraphManager
from superagent.context_models import GraphContext


class GraphQueryEngine:
	"""Run retrieval queries against the knowledge graph and build context."""

	def __init__(self, graph_manager: GraphManager) -> None:
		self.graph_manager = graph_manager

	def _extract_keywords(self, query: str) -> list[str]:
		tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
		# Preserve order while dropping duplicates and very short noise tokens.
		unique_tokens = list(OrderedDict.fromkeys(tokens))
		return [token for token in unique_tokens if len(token) >= 3]

	def find_similar_tasks(self, query: str, limit: int = 5) -> list[dict[str, object]]:
		keywords = self._extract_keywords(query)
		cypher = (
			"MATCH (task:Task) "
			"WITH task, [keyword IN $keywords WHERE "
			"toLower(coalesce(task.query, '')) CONTAINS keyword OR "
			"toLower(coalesce(task.task_type, '')) CONTAINS keyword] AS matched_keywords "
			"WHERE size($keywords) = 0 OR size(matched_keywords) > 0 "
			"RETURN task.task_id AS task_id, "
			"task.query AS query, "
			"task.task_type AS task_type, "
			"task.timestamp AS timestamp, "
			"matched_keywords AS matched_keywords, "
			"size(matched_keywords) AS match_score "
			"ORDER BY match_score DESC, timestamp DESC "
			"LIMIT $limit"
		)
		try:
			results = self.graph_manager.run_read(cypher, {"keywords": keywords, "limit": limit})
			logger.info("Similar tasks found: {}", len(results))
			return results
		except Exception:
			logger.exception("Failed to retrieve similar tasks from graph")
			return []

	def find_related_findings(self, query: str, related_tasks: list[dict[str, object]], limit: int = 8) -> list[dict[str, object]]:
		keywords = self._extract_keywords(query)
		task_ids = [str(task.get("task_id")) for task in related_tasks if task.get("task_id")]
		cypher = (
			"MATCH (finding:Finding) "
			"WHERE (size($task_ids) > 0 AND finding.task_id IN $task_ids) "
			"OR (size($keywords) > 0 AND any(keyword IN $keywords WHERE "
			"toLower(coalesce(finding.content, '')) CONTAINS keyword OR "
			"toLower(coalesce(finding.category, '')) CONTAINS keyword)) "
			"RETURN finding.task_id AS task_id, "
			"finding.source_agent AS source_agent, "
			"finding.category AS category, "
			"finding.content AS content, "
			"finding.confidence AS confidence "
			"ORDER BY confidence DESC "
			"LIMIT $limit"
		)
		try:
			results = self.graph_manager.run_read(
				cypher,
				{"task_ids": task_ids, "keywords": keywords, "limit": limit},
			)
			logger.info("Findings retrieved: {}", len(results))
			return results
		except Exception:
			logger.exception("Failed to retrieve findings from graph")
			return []

	def find_related_risks(self, query: str, related_tasks: list[dict[str, object]], limit: int = 8) -> list[dict[str, object]]:
		keywords = self._extract_keywords(query)
		task_ids = [str(task.get("task_id")) for task in related_tasks if task.get("task_id")]
		cypher = (
			"MATCH (risk:Risk) "
			"WHERE (size($task_ids) > 0 AND risk.task_id IN $task_ids) "
			"OR (size($keywords) > 0 AND any(keyword IN $keywords WHERE "
			"toLower(coalesce(risk.description, '')) CONTAINS keyword OR "
			"toLower(coalesce(risk.severity, '')) CONTAINS keyword)) "
			"RETURN risk.task_id AS task_id, "
			"risk.source_agent AS source_agent, "
			"risk.description AS description, "
			"risk.severity AS severity "
			"LIMIT $limit"
		)
		try:
			results = self.graph_manager.run_read(
				cypher,
				{"task_ids": task_ids, "keywords": keywords, "limit": limit},
			)
			logger.info("Risks retrieved: {}", len(results))
			return results
		except Exception:
			logger.exception("Failed to retrieve risks from graph")
			return []

	def find_related_recommendations(self, query: str, related_tasks: list[dict[str, object]], limit: int = 8) -> list[dict[str, object]]:
		keywords = self._extract_keywords(query)
		task_ids = [str(task.get("task_id")) for task in related_tasks if task.get("task_id")]
		cypher = (
			"MATCH (recommendation:Recommendation) "
			"WHERE (size($task_ids) > 0 AND recommendation.task_id IN $task_ids) "
			"OR (size($keywords) > 0 AND any(keyword IN $keywords WHERE "
			"toLower(coalesce(recommendation.content, '')) CONTAINS keyword OR "
			"toLower(coalesce(recommendation.priority, '')) CONTAINS keyword)) "
			"RETURN recommendation.task_id AS task_id, "
			"recommendation.source_agent AS source_agent, "
			"recommendation.content AS content, "
			"recommendation.priority AS priority "
			"LIMIT $limit"
		)
		try:
			results = self.graph_manager.run_read(
				cypher,
				{"task_ids": task_ids, "keywords": keywords, "limit": limit},
			)
			logger.info("Recommendations retrieved: {}", len(results))
			return results
		except Exception:
			logger.exception("Failed to retrieve recommendations from graph")
			return []

	def _generate_summary(
		self,
		related_tasks: list[dict[str, object]],
		related_findings: list[dict[str, object]],
		related_risks: list[dict[str, object]],
		related_recommendations: list[dict[str, object]],
	) -> str:
		if not related_tasks and not related_findings and not related_risks and not related_recommendations:
			return "No relevant historical graph context found for this query."

		top_findings = [str(item.get("content", "")).strip() for item in related_findings[:3] if item.get("content")]
		top_risks = [str(item.get("description", "")).strip() for item in related_risks[:2] if item.get("description")]
		top_recommendations = [
			str(item.get("content", "")).strip()
			for item in related_recommendations[:2]
			if item.get("content")
		]

		summary_parts: list[str] = []
		if top_findings:
			summary_parts.append("Previous analyses highlighted: " + "; ".join(top_findings))
		if top_risks:
			summary_parts.append("Historical risks include: " + "; ".join(top_risks))
		if top_recommendations:
			summary_parts.append("Historical recommendations include: " + "; ".join(top_recommendations))

		if not summary_parts:
			return "Historical graph records were found, but no concise summary points could be extracted."
		return "\n".join(summary_parts)

	def build_graph_context(self, query: str) -> GraphContext:
		logger.info("Graph retrieval started for query: {}", query)
		related_tasks = self.find_similar_tasks(query)
		related_findings = self.find_related_findings(query, related_tasks)
		related_risks = self.find_related_risks(query, related_tasks)
		related_recommendations = self.find_related_recommendations(query, related_tasks)
		summary = self._generate_summary(
			related_tasks=related_tasks,
			related_findings=related_findings,
			related_risks=related_risks,
			related_recommendations=related_recommendations,
		)
		logger.info("Graph context generated")
		return GraphContext(
			related_tasks=related_tasks,
			related_findings=related_findings,
			related_risks=related_risks,
			related_recommendations=related_recommendations,
			summary=summary,
		)
