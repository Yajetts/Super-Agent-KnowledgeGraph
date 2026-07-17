"""Unit tests for SemanticQueryEngine."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from rag.models import SemanticContext
from rag.query_engine import SemanticQueryEngine


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock vector repository."""
    repo = MagicMock()
    repo.semantic_search = MagicMock()
    repo.count = MagicMock(return_value=10)
    return repo


@pytest.fixture
def query_engine(mock_repository: MagicMock) -> SemanticQueryEngine:
    """Create a SemanticQueryEngine with mocked repository."""
    engine = SemanticQueryEngine()
    engine._repository = mock_repository
    return engine


@pytest.fixture
def sample_search_results() -> list[dict[str, object]]:
    """Sample search results for testing."""
    return [
        {
            "document_id": "doc_1",
            "content": "Electric vehicle market is expanding in India",
            "metadata": {"source_type": "finding", "source_agent": "research_agent"},
            "similarity_score": 0.95,
        },
        {
            "document_id": "doc_2",
            "content": "Government policies support EV adoption",
            "metadata": {"source_type": "recommendation", "source_agent": "strategy_agent"},
            "similarity_score": 0.87,
        },
    ]


def test_search(query_engine: SemanticQueryEngine, mock_repository: MagicMock, sample_search_results: list[dict[str, object]]) -> None:
    """Test basic semantic search."""
    mock_repository.semantic_search.return_value = sample_search_results

    context = query_engine.search("EV market strategy", n_results=5)

    assert isinstance(context, SemanticContext)
    assert len(context.documents) == 2
    assert context.summary != ""
    assert len(context.similarity_scores) == 2
    assert context.similarity_scores[0] == 0.95
    assert context.similarity_scores[1] == 0.87

    mock_repository.semantic_search.assert_called_once_with(
        query="EV market strategy",
        n_results=5,
        source_type=None,
    )


def test_search_with_source_type_filter(query_engine: SemanticQueryEngine, mock_repository: MagicMock) -> None:
    """Test semantic search with source type filter."""
    sample_results = [
        {
            "document_id": "doc_1",
            "content": "Risk about market entry",
            "metadata": {"source_type": "risk", "source_agent": "risk_agent"},
            "similarity_score": 0.92,
        }
    ]
    mock_repository.semantic_search.return_value = sample_results

    context = query_engine.search("market risks", n_results=3, source_type="risk")

    assert len(context.documents) == 1
    assert context.documents[0]["metadata"]["source_type"] == "risk"

    mock_repository.semantic_search.assert_called_once_with(
        query="market risks",
        n_results=3,
        source_type="risk",
    )


def test_search_empty_results(query_engine: SemanticQueryEngine, mock_repository: MagicMock) -> None:
    """Test semantic search with no results."""
    mock_repository.semantic_search.return_value = []

    context = query_engine.search("obscure topic", n_results=5)

    assert len(context.documents) == 0
    assert len(context.similarity_scores) == 0
    assert "No relevant documents found" in context.summary


def test_build_semantic_context(query_engine: SemanticQueryEngine, mock_repository: MagicMock) -> None:
    """Test building semantic context across multiple source types."""
    # Setup different results for different source types
    finding_results = [
        {
            "document_id": "f1",
            "content": "Finding about EV",
            "metadata": {"source_type": "finding"},
            "similarity_score": 0.90,
        }
    ]
    risk_results = [
        {
            "document_id": "r1",
            "content": "Risk about expansion",
            "metadata": {"source_type": "risk"},
            "similarity_score": 0.85,
        }
    ]
    recommendation_results = [
        {
            "document_id": "rec1",
            "content": "Recommendation for strategy",
            "metadata": {"source_type": "recommendation"},
            "similarity_score": 0.88,
        }
    ]

    def mock_semantic_search(query: str, n_results: int, source_type: str | None = None) -> list[dict[str, object]]:
        if source_type == "finding":
            return finding_results
        elif source_type == "risk":
            return risk_results
        elif source_type == "recommendation":
            return recommendation_results
        return []

    mock_repository.semantic_search.side_effect = mock_semantic_search

    context = query_engine.build_semantic_context("EV strategy", n_results=2)

    # Should aggregate results from all source types
    assert len(context.documents) == 3
    assert context.summary != ""

    # Verify all source types are represented
    source_types = {doc["metadata"]["source_type"] for doc in context.documents}
    assert source_types == {"finding", "risk", "recommendation"}


def test_build_semantic_context_with_custom_source_types(query_engine: SemanticQueryEngine, mock_repository: MagicMock) -> None:
    """Test building semantic context with specific source types."""
    sample_results = [
        {
            "document_id": "f1",
            "content": "Finding",
            "metadata": {"source_type": "finding"},
            "similarity_score": 0.90,
        }
    ]
    mock_repository.semantic_search.return_value = sample_results

    context = query_engine.build_semantic_context("query", n_results=5, source_types=["finding"])

    # Should only search findings
    assert mock_repository.semantic_search.call_count == 1
    assert mock_repository.semantic_search.call_args[1]["source_type"] == "finding"


def test_build_semantic_context_sorts_by_similarity(query_engine: SemanticQueryEngine, mock_repository: MagicMock) -> None:
    """Test that results are sorted by similarity score."""
    results = [
        {
            "document_id": "doc_3",
            "content": "Low similarity",
            "metadata": {"source_type": "finding"},
            "similarity_score": 0.70,
        },
        {
            "document_id": "doc_1",
            "content": "High similarity",
            "metadata": {"source_type": "risk"},
            "similarity_score": 0.95,
        },
        {
            "document_id": "doc_2",
            "content": "Medium similarity",
            "metadata": {"source_type": "recommendation"},
            "similarity_score": 0.85,
        },
    ]
    mock_repository.semantic_search.return_value = results

    context = query_engine.build_semantic_context("query", n_results=5, source_types=["finding"])

    # Results should be sorted by similarity (highest first)
    assert context.similarity_scores[0] == 0.95
    assert context.similarity_scores[1] == 0.85
    assert context.similarity_scores[2] == 0.70


def test_build_semantic_context_handles_search_errors(query_engine: SemanticQueryEngine, mock_repository: MagicMock) -> None:
    """Test that search errors are handled gracefully."""
    def mock_search_with_error(query: str, n_results: int, source_type: str | None = None) -> list[dict[str, object]]:
        if source_type == "finding":
            raise RuntimeError("Search failed")
        return [{"document_id": "r1", "content": "Risk", "metadata": {"source_type": "risk"}, "similarity_score": 0.80}]

    mock_repository.semantic_search.side_effect = mock_search_with_error

    # Should not raise, but skip failed source types
    context = query_engine.build_semantic_context("query", n_results=5, source_types=["finding", "risk"])

    # Should still return results from successful searches
    assert len(context.documents) == 1
    assert context.documents[0]["metadata"]["source_type"] == "risk"


def test_build_summary(query_engine: SemanticQueryEngine) -> None:
    """Test summary generation."""
    results = [
        {
            "document_id": "doc_1",
            "content": "Content 1",
            "metadata": {"source_type": "finding"},
            "similarity_score": 0.90,
        },
        {
            "document_id": "doc_2",
            "content": "Content 2",
            "metadata": {"source_type": "risk"},
            "similarity_score": 0.85,
        },
    ]

    summary = query_engine._build_summary("test query", results)

    assert "2 relevant documents" in summary
    assert "finding, risk" in summary
    assert "test query" in summary


def test_build_summary_empty(query_engine: SemanticQueryEngine) -> None:
    """Test summary generation with no results."""
    summary = query_engine._build_summary("test query", [])

    assert "No relevant documents found" in summary
    assert "test query" in summary
