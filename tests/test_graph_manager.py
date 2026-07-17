"""Tests for the Neo4j graph manager."""

from __future__ import annotations

from graph import graph_manager as graph_manager_module
from graph.graph_manager import GraphManager


class FakeDriver:
	def __init__(self) -> None:
		self.closed = False

	def verify_connectivity(self) -> None:
		return None

	def session(self):
		class Session:
			def __enter__(self):
				return self

			def __exit__(self, exc_type, exc, tb):
				return False

			def execute_write(self, callback):
				class Tx:
					def run(self, query, parameters):
						return type("Result", (), {"data": lambda self: [{"query": query, "parameters": parameters}]})()

				return callback(Tx())

			def execute_read(self, callback):
				class Tx:
					def run(self, query, parameters):
						return type("Result", (), {"data": lambda self: [{"exists": True, "query": query, "parameters": parameters}]})()

				return callback(Tx())

		return Session()

	def close(self) -> None:
		self.closed = True


def test_graph_manager_connect_and_close(monkeypatch) -> None:
	"""Ensure the manager opens and closes a Neo4j driver lazily."""
	fake_driver = FakeDriver()
	monkeypatch.setattr(graph_manager_module.GraphDatabase, "driver", lambda *args, **kwargs: fake_driver)

	manager = GraphManager(uri="bolt://example:7687", username="neo4j", password="secret")

	connected_driver = manager.connect()
	assert connected_driver is fake_driver
	manager.close()
	assert fake_driver.closed is True


def test_graph_manager_returns_graph_statistics(monkeypatch) -> None:
	"""Ensure the manager exposes the repository statistics contract."""
	manager = GraphManager(uri="bolt://example:7687", username="neo4j", password="secret")
	monkeypatch.setattr(manager.repository, "get_stats", lambda: {"tasks": 3, "agents": 2, "findings": 4, "risks": 5, "recommendations": 6})

	assert manager.get_stats() == {
		"tasks": 3,
		"agents": 2,
		"findings": 4,
		"risks": 5,
		"recommendations": 6,
	}