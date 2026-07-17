"""Graph-only retrieval backend using the Neo4j query engine."""

from __future__ import annotations

import time
from typing import Any

from graph.context_builder import build_graph_context
from graph.graph_manager import GraphManager
from graph.query_engine import GraphQueryEngine

from evaluation.backends.base import RetrievalBackend, RetrievalOutput, RetrievedItem


def _task_text(task: dict[str, Any]) -> str:
	query = str(task.get("query", "")).strip()
	task_type = str(task.get("task_type", "")).strip()
	if query and task_type:
		return f"{query} ({task_type})"
	return query or task_type or "Task record"


def _flatten_graph_context(context: Any) -> list[RetrievedItem]:
	items: list[RetrievedItem] = []

	for index, task in enumerate(context.related_tasks):
		task_id = str(task.get("task_id", f"task-{index}"))
		items.append(
			RetrievedItem(
				item_id=f"task:{task_id}",
				item_type="task",
				text=_task_text(task),
				metadata={"task_id": task_id},
			)
		)

	for index, finding in enumerate(context.related_findings):
		content = str(finding.get("content", "")).strip()
		if not content:
			continue
		category = str(finding.get("category", "")).strip()
		items.append(
			RetrievedItem(
				item_id=f"finding:{finding.get('task_id', index)}:{index}",
				item_type="finding",
				text=f"{category}: {content}" if category else content,
				metadata={"task_id": finding.get("task_id"), "category": category},
			)
		)

	for index, risk in enumerate(context.related_risks):
		description = str(risk.get("description", "")).strip()
		if not description:
			continue
		severity = str(risk.get("severity", "")).strip()
		items.append(
			RetrievedItem(
				item_id=f"risk:{risk.get('task_id', index)}:{index}",
				item_type="risk",
				text=f"{severity}: {description}" if severity else description,
				metadata={"task_id": risk.get("task_id"), "severity": severity},
			)
		)

	for index, recommendation in enumerate(context.related_recommendations):
		content = str(recommendation.get("content", "")).strip()
		if not content:
			continue
		priority = str(recommendation.get("priority", "")).strip()
		items.append(
			RetrievedItem(
				item_id=f"recommendation:{recommendation.get('task_id', index)}:{index}",
				item_type="recommendation",
				text=f"{priority}: {content}" if priority else content,
				metadata={"task_id": recommendation.get("task_id"), "priority": priority},
			)
		)

	return items


class GraphOnlyBackend(RetrievalBackend):
	"""Baseline backend that retrieves context from Neo4j only."""

	def __init__(self, graph_manager: GraphManager | None = None) -> None:
		self._graph_manager = graph_manager or GraphManager()
		self._query_engine = GraphQueryEngine(self._graph_manager)

	@property
	def name(self) -> str:
		return "graph_only"

	def retrieve(self, query: str) -> RetrievalOutput:
		start = time.perf_counter()
		context = build_graph_context(query, query_engine=self._query_engine)
		elapsed_ms = (time.perf_counter() - start) * 1000
		items = _flatten_graph_context(context)
		return RetrievalOutput(
			query=query,
			items=items,
			summary=context.summary,
			retrieval_time_ms=elapsed_ms,
			raw_context=context.model_dump(),
		)

	def close(self) -> None:
		self._graph_manager.close()
