"""Helpers to build graph context from a natural-language query."""

from __future__ import annotations

from loguru import logger

from graph.graph_manager import GraphManager
from graph.query_engine import GraphQueryEngine
from superagent.context_models import GraphContext


def build_graph_context(query: str, query_engine: GraphQueryEngine | None = None) -> GraphContext:
	"""Retrieve and summarize historical graph context for a query."""
	if not query.strip():
		raise ValueError("Query must not be empty.")

	engine = query_engine
	if engine is None:
		engine = GraphQueryEngine(GraphManager())

	try:
		return engine.build_graph_context(query)
	except Exception:
		logger.exception("Graph context retrieval failed; using empty context")
		return GraphContext(summary="Graph context unavailable due to retrieval failure.")
