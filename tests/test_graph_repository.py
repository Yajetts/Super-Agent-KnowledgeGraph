"""Tests for the Cypher repository layer."""

from __future__ import annotations

from graph.repository import GraphRepository


class RecordingGraphManager:
	def __init__(self) -> None:
		self.write_calls: list[tuple[str, dict[str, object]]] = []
		self.read_calls: list[tuple[str, dict[str, object]]] = []

	def run_write(self, query: str, parameters: dict[str, object] | None = None):
		self.write_calls.append((query, dict(parameters or {})))
		return [{"ok": True}]

	def run_read(self, query: str, parameters: dict[str, object] | None = None):
		self.read_calls.append((query, dict(parameters or {})))
		return [{"exists": True, "tasks": 1, "agents": 2, "findings": 3, "risks": 4, "recommendations": 5}]


def test_repository_merges_task_nodes_without_raw_cypher_leaking_outward() -> None:
	"""Ensure task node writes are handled inside the repository abstraction."""
	manager = RecordingGraphManager()
	repository = GraphRepository(manager)

	repository.create_task_node("task-1", "Analyze EV demand", "business_analysis", "2026-06-09T00:00:00Z")

	assert manager.write_calls[0][0].startswith("MERGE (node:Task")
	assert manager.write_calls[0][1]["task_id"] == "task-1"
	assert manager.write_calls[0][1]["query"] == "Analyze EV demand"


def test_repository_checks_relationship_existence() -> None:
	"""Ensure relationship validation uses a dedicated Cypher read path."""
	manager = RecordingGraphManager()
	repository = GraphRepository(manager)

	assert repository.relationship_exists(
		"TASK_USED_AGENT",
		"Task",
		{"task_id": "task-1"},
		"Agent",
		{"name": "ResearchAgent"},
	)
	assert manager.read_calls[0][0].startswith("MATCH (source:Task")


def test_repository_reports_graph_statistics() -> None:
	"""Ensure the stats query is routed through the repository abstraction."""
	manager = RecordingGraphManager()
	repository = GraphRepository(manager)

	assert repository.get_stats() == {
		"tasks": 1,
		"agents": 2,
		"findings": 3,
		"risks": 4,
		"recommendations": 5,
	}