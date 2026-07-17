"""Unit tests for ContextFusionEngine."""

from __future__ import annotations

import pytest

from rag.context_fusion import ContextFusionEngine


@pytest.fixture
def fusion_engine() -> ContextFusionEngine:
    """Create a ContextFusionEngine instance."""
    return ContextFusionEngine()


@pytest.fixture
def sample_graph_findings() -> list[dict[str, object]]:
    """Sample graph findings."""
    return [
        {
            "task_id": "task_1",
            "source_agent": "ResearchAgent",
            "category": "market",
            "content": "EV adoption is growing rapidly",
            "confidence": 0.9,
        },
        {
            "task_id": "task_2",
            "source_agent": "ResearchAgent",
            "category": "technology",
            "content": "Battery technology is improving",
            "confidence": 0.85,
        },
    ]


@pytest.fixture
def sample_vector_findings() -> list[dict[str, object]]:
    """Sample vector findings."""
    return [
        {
            "document_id": "doc_1",
            "content": "EV adoption is growing rapidly",
            "metadata": {"source_type": "finding", "source_agent": "ResearchAgent"},
            "similarity_score": 0.95,
        },
        {
            "document_id": "doc_2",
            "content": "Charging infrastructure is expanding",
            "metadata": {"source_type": "finding", "source_agent": "ResearchAgent"},
            "similarity_score": 0.88,
        },
    ]


@pytest.fixture
def sample_graph_risks() -> list[dict[str, object]]:
    """Sample graph risks."""
    return [
        {
            "task_id": "task_1",
            "source_agent": "RiskAgent",
            "description": "Policy uncertainty remains",
            "severity": "high",
        }
    ]


@pytest.fixture
def sample_vector_risks() -> list[dict[str, object]]:
    """Sample vector risks."""
    return [
        {
            "document_id": "doc_3",
            "content": "Regulatory changes may impact market",
            "metadata": {"source_type": "risk", "source_agent": "RiskAgent"},
            "similarity_score": 0.92,
        }
    ]


@pytest.fixture
def sample_graph_recommendations() -> list[dict[str, object]]:
    """Sample graph recommendations."""
    return [
        {
            "task_id": "task_1",
            "source_agent": "StrategyAgent",
            "content": "Form strategic partnerships",
            "priority": "high",
        }
    ]


@pytest.fixture
def sample_vector_recommendations() -> list[dict[str, object]]:
    """Sample vector recommendations."""
    return [
        {
            "document_id": "doc_4",
            "content": "Invest in charging infrastructure",
            "metadata": {"source_type": "recommendation", "source_agent": "StrategyAgent"},
            "similarity_score": 0.90,
        }
    ]


def test_merge_results_basic(
    fusion_engine: ContextFusionEngine,
    sample_graph_findings: list[dict[str, object]],
    sample_vector_findings: list[dict[str, object]],
    sample_graph_risks: list[dict[str, object]],
    sample_vector_risks: list[dict[str, object]],
    sample_graph_recommendations: list[dict[str, object]],
    sample_vector_recommendations: list[dict[str, object]],
) -> None:
    """Test basic merging of graph and vector results."""
    merged = fusion_engine.merge_results(
        graph_findings=sample_graph_findings,
        vector_findings=sample_vector_findings,
        graph_risks=sample_graph_risks,
        vector_risks=sample_vector_risks,
        graph_recommendations=sample_graph_recommendations,
        vector_recommendations=sample_vector_recommendations,
    )

    assert "findings" in merged
    assert "risks" in merged
    assert "recommendations" in merged
    assert len(merged["findings"]) > 0
    assert len(merged["risks"]) > 0
    assert len(merged["recommendations"]) > 0


def test_merge_results_deduplicates(
    fusion_engine: ContextFusionEngine,
    sample_graph_findings: list[dict[str, object]],
    sample_vector_findings: list[dict[str, object]],
    sample_graph_risks: list[dict[str, object]],
    sample_vector_risks: list[dict[str, object]],
    sample_graph_recommendations: list[dict[str, object]],
    sample_vector_recommendations: list[dict[str, object]],
) -> None:
    """Test that duplicate content is deduplicated."""
    merged = fusion_engine.merge_results(
        graph_findings=sample_graph_findings,
        vector_findings=sample_vector_findings,
        graph_risks=sample_graph_risks,
        vector_risks=sample_vector_risks,
        graph_recommendations=sample_graph_recommendations,
        vector_recommendations=sample_vector_recommendations,
    )

    # Check for duplicate content in findings
    findings_content = [str(f.get("content", "")).lower() for f in merged["findings"]]
    assert len(findings_content) == len(set(findings_content)), "Findings should be deduplicated"


def test_merge_results_adds_source(
    fusion_engine: ContextFusionEngine,
    sample_graph_findings: list[dict[str, object]],
    sample_vector_findings: list[dict[str, object]],
    sample_graph_risks: list[dict[str, object]],
    sample_vector_risks: list[dict[str, object]],
    sample_graph_recommendations: list[dict[str, object]],
    sample_vector_recommendations: list[dict[str, object]],
) -> None:
    """Test that source information is added to merged results."""
    merged = fusion_engine.merge_results(
        graph_findings=sample_graph_findings,
        vector_findings=sample_vector_findings,
        graph_risks=sample_graph_risks,
        vector_risks=sample_vector_risks,
        graph_recommendations=sample_graph_recommendations,
        vector_recommendations=sample_vector_recommendations,
    )

    # Check that all results have source field
    for finding in merged["findings"]:
        assert "source" in finding
        assert finding["source"] in ["graph", "vector", "hybrid"]

    for risk in merged["risks"]:
        assert "source" in risk
        assert risk["source"] in ["graph", "vector", "hybrid"]

    for recommendation in merged["recommendations"]:
        assert "source" in recommendation
        assert recommendation["source"] in ["graph", "vector", "hybrid"]


def test_merge_results_adds_combined_score(
    fusion_engine: ContextFusionEngine,
    sample_graph_findings: list[dict[str, object]],
    sample_vector_findings: list[dict[str, object]],
    sample_graph_risks: list[dict[str, object]],
    sample_vector_risks: list[dict[str, object]],
    sample_graph_recommendations: list[dict[str, object]],
    sample_vector_recommendations: list[dict[str, object]],
) -> None:
    """Test that combined scores are calculated and added."""
    merged = fusion_engine.merge_results(
        graph_findings=sample_graph_findings,
        vector_findings=sample_vector_findings,
        graph_risks=sample_graph_risks,
        vector_risks=sample_vector_risks,
        graph_recommendations=sample_graph_recommendations,
        vector_recommendations=sample_vector_recommendations,
    )

    # Check that all results have combined_score field
    for finding in merged["findings"]:
        assert "combined_score" in finding
        assert 0 <= finding["combined_score"] <= 1


def test_merge_results_empty_inputs(fusion_engine: ContextFusionEngine) -> None:
    """Test merging with empty inputs."""
    merged = fusion_engine.merge_results(
        graph_findings=[],
        vector_findings=[],
        graph_risks=[],
        vector_risks=[],
        graph_recommendations=[],
        vector_recommendations=[],
    )

    assert merged["findings"] == []
    assert merged["risks"] == []
    assert merged["recommendations"] == []


def test_merge_results_graph_only(
    fusion_engine: ContextFusionEngine,
    sample_graph_findings: list[dict[str, object]],
    sample_graph_risks: list[dict[str, object]],
    sample_graph_recommendations: list[dict[str, object]],
) -> None:
    """Test merging with only graph results."""
    merged = fusion_engine.merge_results(
        graph_findings=sample_graph_findings,
        vector_findings=[],
        graph_risks=sample_graph_risks,
        vector_risks=[],
        graph_recommendations=sample_graph_recommendations,
        vector_recommendations=[],
    )

    assert len(merged["findings"]) == len(sample_graph_findings)
    assert len(merged["risks"]) == len(sample_graph_risks)
    assert len(merged["recommendations"]) == len(sample_graph_recommendations)

    # All should be marked as graph source
    for finding in merged["findings"]:
        assert finding["source"] == "graph"


def test_merge_results_vector_only(
    fusion_engine: ContextFusionEngine,
    sample_vector_findings: list[dict[str, object]],
    sample_vector_risks: list[dict[str, object]],
    sample_vector_recommendations: list[dict[str, object]],
) -> None:
    """Test merging with only vector results."""
    merged = fusion_engine.merge_results(
        graph_findings=[],
        vector_findings=sample_vector_findings,
        graph_risks=[],
        vector_risks=sample_vector_risks,
        graph_recommendations=[],
        vector_recommendations=sample_vector_recommendations,
    )

    assert len(merged["findings"]) == len(sample_vector_findings)
    assert len(merged["risks"]) == len(sample_vector_risks)
    assert len(merged["recommendations"]) == len(sample_vector_recommendations)

    # All should be marked as vector source
    for finding in merged["findings"]:
        assert finding["source"] == "vector"


def test_calculate_graph_score(fusion_engine: ContextFusionEngine) -> None:
    """Test graph score calculation."""
    result = {"confidence": 0.9, "match_score": 2}
    score = fusion_engine._calculate_graph_score(result)

    assert 0 <= score <= 1
    assert score > 0.5  # Base score + confidence boost


def test_calculate_graph_score_no_confidence(fusion_engine: ContextFusionEngine) -> None:
    """Test graph score calculation without confidence."""
    result = {"content": "test"}
    score = fusion_engine._calculate_graph_score(result)

    assert score == 0.5  # Base score only


def test_calculate_vector_score(fusion_engine: ContextFusionEngine) -> None:
    """Test vector score calculation."""
    result = {"similarity_score": 0.95}
    score = fusion_engine._calculate_vector_score(result)

    assert 0 <= score <= 1
    assert score > 0.3


def test_calculate_vector_score_no_similarity(fusion_engine: ContextFusionEngine) -> None:
    """Test vector score calculation without similarity score."""
    result = {"content": "test"}
    score = fusion_engine._calculate_vector_score(result)

    assert score == 0.3  # Default score


def test_rank_by_confidence(fusion_engine: ContextFusionEngine) -> None:
    """Test ranking results by confidence."""
    results = [
        {"content": "low", "combined_score": 0.3},
        {"content": "high", "combined_score": 0.9},
        {"content": "medium", "combined_score": 0.6},
    ]

    ranked = fusion_engine.rank_by_confidence(results, limit=10)

    assert len(ranked) == 3
    assert ranked[0]["combined_score"] == 0.9
    assert ranked[1]["combined_score"] == 0.6
    assert ranked[2]["combined_score"] == 0.3


def test_rank_by_confidence_with_limit(fusion_engine: ContextFusionEngine) -> None:
    """Test ranking results with a limit."""
    results = [
        {"content": "1", "combined_score": 0.9},
        {"content": "2", "combined_score": 0.8},
        {"content": "3", "combined_score": 0.7},
        {"content": "4", "combined_score": 0.6},
        {"content": "5", "combined_score": 0.5},
    ]

    ranked = fusion_engine.rank_by_confidence(results, limit=3)

    assert len(ranked) == 3
    assert ranked[0]["combined_score"] == 0.9
    assert ranked[1]["combined_score"] == 0.8
    assert ranked[2]["combined_score"] == 0.7
