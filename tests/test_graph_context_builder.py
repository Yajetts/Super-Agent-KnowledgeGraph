"""Tests for graph context builder helper."""

from __future__ import annotations

import pytest

from graph.context_builder import build_graph_context
from superagent.context_models import GraphContext


class StubQueryEngine:
	def build_graph_context(self, query: str) -> GraphContext:
		return GraphContext(
			related_tasks=[{"task_id": "task-1", "query": query}],
			related_findings=[{"content": "Finding one"}],
			related_risks=[{"description": "Risk one"}],
			related_recommendations=[{"content": "Recommendation one"}],
			summary="Summary text",
		)


class FailingQueryEngine:
	def build_graph_context(self, query: str) -> GraphContext:
		raise RuntimeError("invalid graph query")


def test_build_graph_context_returns_engine_result() -> None:
	"""Ensure helper passes through a successful retrieval result."""
	context = build_graph_context("Tesla expansion", query_engine=StubQueryEngine())

	assert context.related_tasks[0]["task_id"] == "task-1"
	assert context.summary == "Summary text"


def test_build_graph_context_rejects_empty_query() -> None:
	"""Ensure helper validates query input."""
	with pytest.raises(ValueError):
		build_graph_context("   ", query_engine=StubQueryEngine())


def test_build_graph_context_handles_engine_failures() -> None:
	"""Ensure helper gracefully falls back on query failures."""
	context = build_graph_context("Tesla expansion", query_engine=FailingQueryEngine())

	assert context.related_tasks == []
	assert "unavailable" in context.summary
