"""Tests for the GraphRAG API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api import routes
from app.main import app


class FakeGraphRAGController:
    """Fake controller for testing GraphRAG endpoints."""

    def get_graphrag_context(self, query: str):
        """Return fake GraphRAG context."""
        return {
            "query": query,
            "graph_results": [
                {"task_id": "task_1", "query": query, "match_score": 2}
            ],
            "vector_results": [
                {
                    "document_id": "doc_1",
                    "content": f"Content for {query}",
                    "metadata": {"source_type": "finding"},
                    "similarity_score": 0.95,
                }
            ],
            "merged_findings": [
                {
                    "content": f"Finding for {query}",
                    "category": "market",
                    "source": "graph",
                    "combined_score": 0.9,
                }
            ],
            "merged_risks": [
                {
                    "description": f"Risk for {query}",
                    "severity": "high",
                    "source": "vector",
                    "combined_score": 0.85,
                }
            ],
            "merged_recommendations": [
                {
                    "content": f"Recommendation for {query}",
                    "priority": "high",
                    "source": "hybrid",
                    "combined_score": 0.92,
                }
            ],
            "context_summary": f"Summary for {query}",
            "retrieval_metadata": {
                "graph_tasks": 1,
                "graph_findings": 1,
                "vector_documents": 1,
                "fusion_results": 3,
                "graph_available": True,
                "vector_available": True,
            },
        }

    def get_graphrag_stats(self):
        """Return fake GraphRAG stats."""
        return {
            "graph_nodes": 500,
            "vector_documents": 1200,
            "graph_available": True,
            "vector_available": True,
        }

    def close(self) -> None:
        """Close resources."""
        return None


def test_graphrag_context_endpoint_returns_retrieval_payload() -> None:
    """Ensure the GraphRAG context endpoint returns retrieval context for a query."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    response = client.get("/graphrag/context", params={"query": "EV market strategy"})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "EV market strategy"
    assert len(body["graph_results"]) == 1
    assert len(body["vector_results"]) == 1
    assert len(body["merged_findings"]) == 1
    assert len(body["merged_risks"]) == 1
    assert len(body["merged_recommendations"]) == 1
    assert body["context_summary"] != ""
    assert body["retrieval_metadata"]["graph_available"] is True
    assert body["retrieval_metadata"]["vector_available"] is True


def test_graphrag_stats_endpoint_returns_counts() -> None:
    """Ensure the GraphRAG stats endpoint returns the expected shape."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    response = client.get("/graphrag/stats")

    assert response.status_code == 200
    assert response.json() == {
        "graph_nodes": 500,
        "vector_documents": 1200,
        "graph_available": True,
        "vector_available": True,
    }


def test_graphrag_context_endpoint_with_empty_query() -> None:
    """Test GraphRAG context endpoint with empty query."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    response = client.get("/graphrag/context", params={"query": ""})

    # Should still return 200 with empty results
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == ""


def test_graphrag_context_endpoint_with_special_characters() -> None:
    """Test GraphRAG context endpoint with special characters in query."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    query = "EV market & strategy (2024)"
    response = client.get("/graphrag/context", params={"query": query})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == query


def test_graphrag_stats_endpoint_structure() -> None:
    """Ensure GraphRAG stats endpoint has correct structure."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    response = client.get("/graphrag/stats")

    assert response.status_code == 200
    body = response.json()
    assert "graph_nodes" in body
    assert "vector_documents" in body
    assert "graph_available" in body
    assert "vector_available" in body
    assert isinstance(body["graph_nodes"], int)
    assert isinstance(body["vector_documents"], int)
    assert isinstance(body["graph_available"], bool)
    assert isinstance(body["vector_available"], bool)


def test_graphrag_context_includes_retrieval_metadata() -> None:
    """Ensure GraphRAG context includes retrieval metadata."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    response = client.get("/graphrag/context", params={"query": "test query"})

    assert response.status_code == 200
    body = response.json()
    assert "retrieval_metadata" in body
    metadata = body["retrieval_metadata"]
    assert "graph_tasks" in metadata
    assert "graph_findings" in metadata
    assert "vector_documents" in metadata
    assert "fusion_results" in metadata
    assert "graph_available" in metadata
    assert "vector_available" in metadata


def test_graphrag_context_merged_results_have_scores() -> None:
    """Ensure merged results have combined scores."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    response = client.get("/graphrag/context", params={"query": "test query"})

    assert response.status_code == 200
    body = response.json()

    # Check that merged results have combined_score
    for finding in body["merged_findings"]:
        assert "combined_score" in finding
        assert 0 <= finding["combined_score"] <= 1

    for risk in body["merged_risks"]:
        assert "combined_score" in risk
        assert 0 <= risk["combined_score"] <= 1

    for recommendation in body["merged_recommendations"]:
        assert "combined_score" in recommendation
        assert 0 <= recommendation["combined_score"] <= 1


def test_graphrag_context_merged_results_have_source() -> None:
    """Ensure merged results have source information."""
    routes.controller = FakeGraphRAGController()
    client = TestClient(app)

    response = client.get("/graphrag/context", params={"query": "test query"})

    assert response.status_code == 200
    body = response.json()

    # Check that merged results have source field
    for finding in body["merged_findings"]:
        assert "source" in finding
        assert finding["source"] in ["graph", "vector", "hybrid"]

    for risk in body["merged_risks"]:
        assert "source" in risk
        assert risk["source"] in ["graph", "vector", "hybrid"]

    for recommendation in body["merged_recommendations"]:
        assert "source" in recommendation
        assert recommendation["source"] in ["graph", "vector", "hybrid"]
