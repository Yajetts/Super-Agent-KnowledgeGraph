"""GraphRAG retrieval backend for Phase 7 evaluation."""

from __future__ import annotations

import time
from typing import Any

from graph.graph_manager import GraphManager
from graph.query_engine import GraphQueryEngine
from rag.graphrag import GraphRAGEngine
from rag.query_engine import SemanticQueryEngine

from evaluation.backends.base import RetrievalBackend, RetrievalOutput, RetrievedItem


def _flatten_graphrag_context(context: Any) -> list[RetrievedItem]:
	"""Flatten GraphRAG context into RetrievedItem list."""
	items: list[RetrievedItem] = []

	# Add graph results (tasks)
	for index, task in enumerate(context.graph_results):
		task_id = str(task.get("task_id", f"task-{index}"))
		query = str(task.get("query", "")).strip()
		task_type = str(task.get("task_type", "")).strip()
		if query and task_type:
			items.append(
				RetrievedItem(
					item_id=f"task:{task_id}",
					item_type="task",
					text=f"{query} ({task_type})",
					metadata={"task_id": task_id, "source": "graph"},
				)
			)

	# Add vector results (documents)
	for index, doc in enumerate(context.vector_results):
		doc_id = str(doc.get("id", f"doc-{index}"))
		content = str(doc.get("content", "")).strip()
		if content:
			items.append(
				RetrievedItem(
					item_id=f"doc:{doc_id}",
					item_type="document",
					text=content,
					metadata={"doc_id": doc_id, "source": "vector"},
				)
			)

	# Add merged findings
	for index, finding in enumerate(context.merged_findings):
		content = str(finding.get("content", "")).strip()
		if not content:
			continue
		category = str(finding.get("category", "")).strip()
		source = str(finding.get("source", "unknown")).strip()
		items.append(
			RetrievedItem(
				item_id=f"finding:{index}",
				item_type="finding",
				text=f"{category}: {content}" if category else content,
				metadata={"category": category, "source": source},
			)
		)

	# Add merged risks
	for index, risk in enumerate(context.merged_risks):
		description = str(risk.get("description", "")).strip()
		if not description:
			continue
		severity = str(risk.get("severity", "")).strip()
		source = str(risk.get("source", "unknown")).strip()
		items.append(
			RetrievedItem(
				item_id=f"risk:{index}",
				item_type="risk",
				text=f"{severity}: {description}" if severity else description,
				metadata={"severity": severity, "source": source},
			)
		)

	# Add merged recommendations
	for index, recommendation in enumerate(context.merged_recommendations):
		content = str(recommendation.get("content", "")).strip()
		if not content:
			continue
		priority = str(recommendation.get("priority", "")).strip()
		source = str(recommendation.get("source", "unknown")).strip()
		items.append(
			RetrievedItem(
				item_id=f"recommendation:{index}",
				item_type="recommendation",
				text=f"{priority}: {content}" if priority else content,
				metadata={"priority": priority, "source": source},
			)
		)

	return items


class GraphRAGBackend(RetrievalBackend):
	"""GraphRAG backend that fuses graph and vector retrieval."""

	def __init__(
		self,
		graph_manager: GraphManager | None = None,
		semantic_query_engine: SemanticQueryEngine | None = None,
	) -> None:
		"""Initialize the GraphRAG backend.

		Args:
			graph_manager: Optional graph manager for graph retrieval.
			semantic_query_engine: Optional semantic query engine for vector retrieval.
		"""
		self._graph_manager = graph_manager or GraphManager()
		graph_query_engine = GraphQueryEngine(self._graph_manager)
		self._semantic_query_engine = semantic_query_engine or SemanticQueryEngine()
		self._graphrag_engine = GraphRAGEngine(
			graph_query_engine=graph_query_engine,
			semantic_query_engine=self._semantic_query_engine,
		)

	@property
	def name(self) -> str:
		return "graphrag"

	def retrieve(self, query: str) -> RetrievalOutput:
		"""Execute GraphRAG retrieval for a query.

		Args:
			query: The user query.

		Returns:
			RetrievalOutput with fused graph and vector context items.
		"""
		start = time.perf_counter()
		context = self._graphrag_engine.retrieve_context(query)
		elapsed_ms = (time.perf_counter() - start) * 1000
		items = _flatten_graphrag_context(context)

		# Build summary with retrieval metadata
		metadata = context.retrieval_metadata or {}
		summary_parts = [
			f"Graph retrieval: {metadata.get('graph_tasks', 0)} tasks, "
			f"{metadata.get('graph_findings', 0)} findings/risks/recommendations",
			f"Vector retrieval: {metadata.get('vector_documents', 0)} documents",
			f"Fused context: {metadata.get('fusion_results', 0)} total items",
		]
		summary = ". ".join(summary_parts)

		return RetrievalOutput(
			query=query,
			items=items,
			summary=summary,
			retrieval_time_ms=elapsed_ms,
			raw_context=context.model_dump(),
		)

	def close(self) -> None:
		"""Release backend resources."""
		self._graph_manager.close()

