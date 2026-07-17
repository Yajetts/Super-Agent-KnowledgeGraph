"""Tests for graph retrieval and context generation."""

from __future__ import annotations

from graph.query_engine import GraphQueryEngine


class StubGraphManager:
	def __init__(self) -> None:
		self.calls: list[tuple[str, dict[str, object]]] = []

	def run_read(self, query: str, parameters: dict[str, object] | None = None):
		params = dict(parameters or {})
		self.calls.append((query, params))
		if "MATCH (task:Task)" in query:
			return [
				{
					"task_id": "task-1",
					"query": "Tesla market entry in India",
					"task_type": "market_analysis",
					"timestamp": "2026-05-01T00:00:00Z",
					"matched_keywords": ["tesla", "india"],
					"match_score": 2,
				}
			]
		if "MATCH (finding:Finding)" in query:
			return [{"task_id": "task-1", "source_agent": "ResearchAgent", "category": "market", "content": "EV adoption is increasing", "confidence": 0.9}]
		if "MATCH (risk:Risk)" in query:
			return [{"task_id": "task-1", "source_agent": "RiskAgent", "description": "Infrastructure constraints", "severity": "high"}]
		if "MATCH (recommendation:Recommendation)" in query:
			return [{"task_id": "task-1", "source_agent": "StrategyAgent", "content": "Partner with local distributors", "priority": "high"}]
		return []


class FailingGraphManager:
	def run_read(self, query: str, parameters: dict[str, object] | None = None):
		raise RuntimeError("neo4j unavailable")


def test_find_similar_tasks_uses_keyword_query() -> None:
	"""Ensure similar task retrieval runs against Task nodes with keyword parameters."""
	engine = GraphQueryEngine(StubGraphManager())

	results = engine.find_similar_tasks("Analyze Tesla expansion into India")

	assert len(results) == 1
	assert results[0]["task_id"] == "task-1"


def test_build_graph_context_collects_findings_risks_and_recommendations() -> None:
	"""Ensure graph context assembly collects all related node categories."""
	engine = GraphQueryEngine(StubGraphManager())

	context = engine.build_graph_context("Analyze Tesla expansion into India")

	assert context.related_tasks[0]["task_id"] == "task-1"
	assert context.related_findings[0]["content"] == "EV adoption is increasing"
	assert context.related_risks[0]["description"] == "Infrastructure constraints"
	assert context.related_recommendations[0]["content"] == "Partner with local distributors"
	assert "Historical risks include" in context.summary


def test_graph_query_engine_gracefully_falls_back_on_failures() -> None:
	"""Ensure retrieval methods fail safely when Neo4j calls raise errors."""
	engine = GraphQueryEngine(FailingGraphManager())

	context = engine.build_graph_context("Analyze Tesla expansion into India")

	assert context.related_tasks == []
	assert context.related_findings == []
	assert context.related_risks == []
	assert context.related_recommendations == []
	assert context.summary == "No relevant historical graph context found for this query."
