"""Tests for the graph API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api import routes
from app.main import app


class FakeController:
	def get_graph_stats(self):
		return {"tasks": 10, "agents": 4, "findings": 42, "risks": 18, "recommendations": 25}

	def get_graph_schema(self):
		return {
			"node_types": [
				{"label": "Task", "properties": ["task_id", "query", "task_type", "timestamp"]},
			],
			"relationship_types": [
				{"type": "TASK_USED_AGENT", "source": "Task", "target": "Agent"},
			],
			"agents": [],
		}

	def get_graph_context(self, query: str):
		return {
			"related_tasks": [{"task_id": "task-1", "query": query, "task_type": "business_analysis"}],
			"related_findings": [{"content": "EV adoption rising", "category": "market"}],
			"related_risks": [{"description": "Policy volatility", "severity": "high"}],
			"related_recommendations": [{"content": "Partner locally", "priority": "high"}],
			"summary": "Historical EV expansion work suggests partnerships reduce market entry risk.",
		}

	def close(self) -> None:
		return None


def test_graph_stats_endpoint_returns_counts() -> None:
	"""Ensure the graph statistics endpoint returns the expected shape."""
	routes.controller = FakeController()
	client = TestClient(app)

	response = client.get("/graph/stats")

	assert response.status_code == 200
	assert response.json() == {"tasks": 10, "agents": 4, "findings": 42, "risks": 18, "recommendations": 25}


def test_graph_schema_endpoint_returns_schema_summary() -> None:
	"""Ensure the graph schema endpoint returns a schema summary payload."""
	routes.controller = FakeController()
	client = TestClient(app)

	response = client.get("/graph/schema")

	assert response.status_code == 200
	assert response.json()["node_types"][0]["label"] == "Task"


def test_graph_context_endpoint_returns_retrieval_payload() -> None:
	"""Ensure the graph context endpoint returns retrieval context for a query."""
	routes.controller = FakeController()
	client = TestClient(app)

	response = client.get("/graph/context", params={"query": "Tesla expansion"})

	assert response.status_code == 200
	body = response.json()
	assert body["related_tasks"][0]["task_id"] == "task-1"
	assert "Historical EV expansion work" in body["summary"]