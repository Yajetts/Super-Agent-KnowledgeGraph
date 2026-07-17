"""Unit tests for GraphRAGEngine."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from rag.graphrag import GraphRAGEngine
from superagent.context_models import GraphRAGContext


@pytest.fixture
def mock_graph_query_engine() -> MagicMock:
    """Create a mock graph query engine."""
    engine = MagicMock()
    engine.build_graph_context = MagicMock()
    return engine


@pytest.fixture
def mock_semantic_query_engine() -> MagicMock:
    """Create a mock semantic query engine."""
    engine = MagicMock()
    engine.build_semantic_context = MagicMock()
    return engine


@pytest.fixture
def graphrag_engine(
    mock_graph_query_engine: MagicMock, mock_semantic_query_engine: MagicMock
) -> GraphRAGEngine:
    """Create a GraphRAGEngine with mocked dependencies."""
    engine = GraphRAGEngine(
        graph_query_engine=mock_graph_query_engine,
        semantic_query_engine=mock_semantic_query_engine,
    )
    return engine


@pytest.fixture
def sample_graph_context() -> MagicMock:
    """Create a sample graph context."""
    context = MagicMock()
    context.related_tasks = [
        {"task_id": "task_1", "query": "EV market analysis", "match_score": 2}
    ]
    context.related_findings = [
        {
            "task_id": "task_1",
            "source_agent": "ResearchAgent",
            "category": "market",
            "content": "EV adoption is growing",
            "confidence": 0.9,
        }
    ]
    context.related_risks = [
        {
            "task_id": "task_1",
            "source_agent": "RiskAgent",
            "description": "Policy uncertainty",
            "severity": "high",
        }
    ]
    context.related_recommendations = [
        {
            "task_id": "task_1",
            "source_agent": "StrategyAgent",
            "content": "Form partnerships",
            "priority": "high",
        }
    ]
    context.summary = "Historical analysis shows growing EV adoption."
    return context


@pytest.fixture
def sample_semantic_context() -> MagicMock:
    """Create a sample semantic context."""
    context = MagicMock()
    context.documents = [
        {
            "document_id": "doc_1",
            "content": "Electric vehicle market expansion",
            "metadata": {"source_type": "finding", "source_agent": "ResearchAgent"},
            "similarity_score": 0.95,
        },
        {
            "document_id": "doc_2",
            "content": "Infrastructure challenges",
            "metadata": {"source_type": "risk", "source_agent": "RiskAgent"},
            "similarity_score": 0.88,
        },
        {
            "document_id": "doc_3",
            "content": "Strategic partnerships recommended",
            "metadata": {"source_type": "recommendation", "source_agent": "StrategyAgent"},
            "similarity_score": 0.92,
        },
    ]
    context.summary = "Found 3 relevant documents."
    context.similarity_scores = [0.95, 0.88, 0.92]
    return context


def test_retrieve_context_with_both_sources(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
    mock_semantic_query_engine: MagicMock,
    sample_graph_context: MagicMock,
    sample_semantic_context: MagicMock,
) -> None:
    """Test GraphRAG context retrieval with both graph and vector sources."""
    mock_graph_query_engine.build_graph_context.return_value = sample_graph_context
    mock_semantic_query_engine.build_semantic_context.return_value = sample_semantic_context

    context = graphrag_engine.retrieve_context("EV market strategy")

    assert isinstance(context, GraphRAGContext)
    assert context.query == "EV market strategy"
    assert len(context.graph_results) == 1
    assert len(context.vector_results) == 3
    assert len(context.merged_findings) > 0
    assert len(context.merged_risks) > 0
    assert len(context.merged_recommendations) > 0
    assert context.context_summary != ""
    assert context.retrieval_metadata["graph_available"] is True
    assert context.retrieval_metadata["vector_available"] is True

    mock_graph_query_engine.build_graph_context.assert_called_once_with("EV market strategy")
    mock_semantic_query_engine.build_semantic_context.assert_called_once_with("EV market strategy")


def test_retrieve_context_with_graph_only(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
    mock_semantic_query_engine: MagicMock,
    sample_graph_context: MagicMock,
) -> None:
    """Test GraphRAG context retrieval with only graph source."""
    mock_graph_query_engine.build_graph_context.return_value = sample_graph_context
    mock_semantic_query_engine.build_semantic_context.side_effect = RuntimeError("Vector DB unavailable")

    context = graphrag_engine.retrieve_context("EV market strategy")

    assert isinstance(context, GraphRAGContext)
    assert context.retrieval_metadata["graph_available"] is True
    assert context.retrieval_metadata["vector_available"] is False
    assert "vector_error" in context.retrieval_metadata


def test_retrieve_context_with_vector_only(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
    mock_semantic_query_engine: MagicMock,
    sample_semantic_context: MagicMock,
) -> None:
    """Test GraphRAG context retrieval with only vector source."""
    mock_graph_query_engine.build_graph_context.side_effect = RuntimeError("Graph DB unavailable")
    mock_semantic_query_engine.build_semantic_context.return_value = sample_semantic_context

    context = graphrag_engine.retrieve_context("EV market strategy")

    assert isinstance(context, GraphRAGContext)
    assert context.retrieval_metadata["graph_available"] is False
    assert context.retrieval_metadata["vector_available"] is True
    assert "graph_error" in context.retrieval_metadata


def test_retrieve_context_empty_results(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
    mock_semantic_query_engine: MagicMock,
) -> None:
    """Test GraphRAG context retrieval with no results."""
    empty_graph_context = MagicMock()
    empty_graph_context.related_tasks = []
    empty_graph_context.related_findings = []
    empty_graph_context.related_risks = []
    empty_graph_context.related_recommendations = []
    empty_graph_context.summary = ""

    empty_semantic_context = MagicMock()
    empty_semantic_context.documents = []
    empty_semantic_context.summary = ""

    mock_graph_query_engine.build_graph_context.return_value = empty_graph_context
    mock_semantic_query_engine.build_semantic_context.return_value = empty_semantic_context

    context = graphrag_engine.retrieve_context("obscure query")

    assert isinstance(context, GraphRAGContext)
    assert len(context.graph_results) == 0
    assert len(context.vector_results) == 0
    assert context.context_summary != ""


def test_get_simple_context_summary(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
    mock_semantic_query_engine: MagicMock,
    sample_graph_context: MagicMock,
    sample_semantic_context: MagicMock,
) -> None:
    """Test getting a simple context summary."""
    mock_graph_query_engine.build_graph_context.return_value = sample_graph_context
    mock_semantic_query_engine.build_semantic_context.return_value = sample_semantic_context

    summary = graphrag_engine.get_simple_context_summary("EV market strategy")

    assert isinstance(summary, str)
    assert len(summary) > 0


def test_get_simple_context_summary_with_error(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
) -> None:
    """Test simple context summary when retrieval fails."""
    mock_graph_query_engine.build_graph_context.side_effect = RuntimeError("Retrieval failed")

    summary = graphrag_engine.get_simple_context_summary("test query")

    assert "Context retrieval failed" in summary


def test_get_stats(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
) -> None:
    """Test getting GraphRAG system statistics."""
    mock_graph_manager = MagicMock()
    mock_graph_manager.get_stats.return_value = {
        "tasks": 10,
        "findings": 50,
        "risks": 20,
        "recommendations": 30,
    }
    mock_graph_query_engine.graph_manager = mock_graph_manager

    stats = graphrag_engine.get_stats()

    assert isinstance(stats, dict)
    assert "graph_available" in stats
    assert "vector_available" in stats
    assert stats["graph_available"] is True


def test_get_stats_with_graph_error(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
) -> None:
    """Test getting stats when graph stats fail."""
    mock_graph_manager = MagicMock()
    mock_graph_manager.get_stats.side_effect = RuntimeError("Graph stats failed")
    mock_graph_query_engine.graph_manager = mock_graph_manager

    stats = graphrag_engine.get_stats()

    assert stats["graph_nodes"] == 0


def test_retrieve_context_deduplicates_results(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
    mock_semantic_query_engine: MagicMock,
) -> None:
    """Test that duplicate results are properly deduplicated."""
    # Create contexts with overlapping content
    graph_context = MagicMock()
    graph_context.related_tasks = []
    graph_context.related_findings = [
        {
            "task_id": "task_1",
            "content": "EV market is growing",
            "category": "market",
            "confidence": 0.9,
        }
    ]
    graph_context.related_risks = []
    graph_context.related_recommendations = []

    semantic_context = MagicMock()
    semantic_context.documents = [
        {
            "document_id": "doc_1",
            "content": "EV market is growing",
            "metadata": {"source_type": "finding"},
            "similarity_score": 0.95,
        }
    ]

    mock_graph_query_engine.build_graph_context.return_value = graph_context
    mock_semantic_query_engine.build_semantic_context.return_value = semantic_context

    context = graphrag_engine.retrieve_context("EV market")

    # Should deduplicate based on content
    assert len(context.merged_findings) == 1


def test_retrieve_context_ranks_by_score(
    graphrag_engine: GraphRAGEngine,
    mock_graph_query_engine: MagicMock,
    mock_semantic_query_engine: MagicMock,
) -> None:
    """Test that results are ranked by combined score."""
    graph_context = MagicMock()
    graph_context.related_tasks = []
    graph_context.related_findings = [
        {"content": "Low priority finding", "confidence": 0.5},
        {"content": "High priority finding", "confidence": 0.9},
    ]
    graph_context.related_risks = []
    graph_context.related_recommendations = []

    semantic_context = MagicMock()
    semantic_context.documents = []

    mock_graph_query_engine.build_graph_context.return_value = graph_context
    mock_semantic_query_engine.build_semantic_context.return_value = semantic_context

    context = graphrag_engine.retrieve_context("test query")

    # Results should be ranked by score
    if len(context.merged_findings) >= 2:
        scores = [f.get("combined_score", 0) for f in context.merged_findings]
        assert scores[0] >= scores[1]
