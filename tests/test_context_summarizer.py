"""Unit tests for ContextSummarizer."""

from __future__ import annotations

import pytest

from rag.context_summarizer import ContextSummarizer


@pytest.fixture
def summarizer() -> ContextSummarizer:
    """Create a ContextSummarizer instance."""
    return ContextSummarizer()


@pytest.fixture
def sample_merged_findings() -> list[dict[str, object]]:
    """Sample merged findings."""
    return [
        {
            "content": "EV adoption is growing rapidly in emerging markets",
            "category": "market",
            "source": "graph",
            "combined_score": 0.9,
        },
        {
            "content": "Battery technology improvements are driving cost reductions",
            "category": "technology",
            "source": "vector",
            "combined_score": 0.85,
        },
        {
            "content": "Government incentives are accelerating adoption",
            "category": "policy",
            "source": "hybrid",
            "combined_score": 0.88,
        },
    ]


@pytest.fixture
def sample_merged_risks() -> list[dict[str, object]]:
    """Sample merged risks."""
    return [
        {
            "description": "Policy uncertainty may impact long-term planning",
            "severity": "high",
            "source": "graph",
            "combined_score": 0.92,
        },
        {
            "description": "Infrastructure limitations could slow adoption",
            "severity": "medium",
            "source": "vector",
            "combined_score": 0.78,
        },
    ]


@pytest.fixture
def sample_merged_recommendations() -> list[dict[str, object]]:
    """Sample merged recommendations."""
    return [
        {
            "content": "Form strategic partnerships with local manufacturers",
            "priority": "high",
            "source": "graph",
            "combined_score": 0.95,
        },
        {
            "content": "Invest in charging infrastructure development",
            "priority": "high",
            "source": "vector",
            "combined_score": 0.90,
        },
    ]


def test_generate_summary_with_all_results(
    summarizer: ContextSummarizer,
    sample_merged_findings: list[dict[str, object]],
    sample_merged_risks: list[dict[str, object]],
    sample_merged_recommendations: list[dict[str, object]],
) -> None:
    """Test summary generation with all result types."""
    summary = summarizer.generate_summary(
        query="EV market strategy",
        graph_results=[{"task_id": "task_1"}],
        vector_results=[{"document_id": "doc_1"}],
        merged_findings=sample_merged_findings,
        merged_risks=sample_merged_risks,
        merged_recommendations=sample_merged_recommendations,
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "EV market strategy" in summary
    assert "Key findings" in summary or "findings" in summary.lower()
    assert "Related risks" in summary or "risks" in summary.lower()
    assert "Common recommendations" in summary or "recommendations" in summary.lower()


def test_generate_summary_with_findings_only(
    summarizer: ContextSummarizer,
    sample_merged_findings: list[dict[str, object]],
) -> None:
    """Test summary generation with only findings."""
    summary = summarizer.generate_summary(
        query="test query",
        graph_results=[],
        vector_results=[],
        merged_findings=sample_merged_findings,
        merged_risks=[],
        merged_recommendations=[],
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "findings" in summary.lower()


def test_generate_summary_with_risks_only(
    summarizer: ContextSummarizer,
    sample_merged_risks: list[dict[str, object]],
) -> None:
    """Test summary generation with only risks."""
    summary = summarizer.generate_summary(
        query="test query",
        graph_results=[],
        vector_results=[],
        merged_findings=[],
        merged_risks=sample_merged_risks,
        merged_recommendations=[],
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "risks" in summary.lower()


def test_generate_summary_with_recommendations_only(
    summarizer: ContextSummarizer,
    sample_merged_recommendations: list[dict[str, object]],
) -> None:
    """Test summary generation with only recommendations."""
    summary = summarizer.generate_summary(
        query="test query",
        graph_results=[],
        vector_results=[],
        merged_findings=[],
        merged_risks=[],
        merged_recommendations=sample_merged_recommendations,
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "recommendations" in summary.lower()


def test_generate_summary_empty_results(summarizer: ContextSummarizer) -> None:
    """Test summary generation with no results."""
    summary = summarizer.generate_summary(
        query="test query",
        graph_results=[],
        vector_results=[],
        merged_findings=[],
        merged_risks=[],
        merged_recommendations=[],
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "No relevant context found" in summary or "proceeding with fresh analysis" in summary.lower()


def test_generate_summary_includes_retrieval_stats(summarizer: ContextSummarizer) -> None:
    """Test that summary includes retrieval statistics."""
    summary = summarizer.generate_summary(
        query="test query",
        graph_results=[{"task_id": "task_1"}, {"task_id": "task_2"}],
        vector_results=[{"document_id": "doc_1"}, {"document_id": "doc_2"}, {"document_id": "doc_3"}],
        merged_findings=[],
        merged_risks=[],
        merged_recommendations=[],
    )

    assert "2 graph results" in summary or "graph" in summary.lower()
    assert "3 vector results" in summary or "vector" in summary.lower()


def test_format_findings(summarizer: ContextSummarizer) -> None:
    """Test findings formatting."""
    findings = [
        {
            "content": "Test finding 1",
            "category": "market",
            "source": "graph",
            "combined_score": 0.9,
        },
        {
            "content": "Test finding 2",
            "category": "technology",
            "source": "vector",
            "combined_score": 0.85,
        },
    ]

    formatted = summarizer._format_findings(findings)

    assert isinstance(formatted, str)
    assert len(formatted) > 0
    assert "Test finding 1" in formatted
    assert "Test finding 2" in formatted
    assert "market" in formatted
    assert "technology" in formatted
    assert "graph" in formatted
    assert "vector" in formatted


def test_format_findings_empty(summarizer: ContextSummarizer) -> None:
    """Test findings formatting with empty list."""
    formatted = summarizer._format_findings([])
    assert formatted == ""


def test_format_risks(summarizer: ContextSummarizer) -> None:
    """Test risks formatting."""
    risks = [
        {
            "description": "Test risk 1",
            "severity": "high",
            "source": "graph",
            "combined_score": 0.92,
        },
        {
            "description": "Test risk 2",
            "severity": "medium",
            "source": "vector",
            "combined_score": 0.78,
        },
    ]

    formatted = summarizer._format_risks(risks)

    assert isinstance(formatted, str)
    assert len(formatted) > 0
    assert "Test risk 1" in formatted
    assert "Test risk 2" in formatted
    assert "high" in formatted
    assert "medium" in formatted


def test_format_risks_empty(summarizer: ContextSummarizer) -> None:
    """Test risks formatting with empty list."""
    formatted = summarizer._format_risks([])
    assert formatted == ""


def test_format_recommendations(summarizer: ContextSummarizer) -> None:
    """Test recommendations formatting."""
    recommendations = [
        {
            "content": "Test recommendation 1",
            "priority": "high",
            "source": "graph",
            "combined_score": 0.95,
        },
        {
            "content": "Test recommendation 2",
            "priority": "medium",
            "source": "vector",
            "combined_score": 0.90,
        },
    ]

    formatted = summarizer._format_recommendations(recommendations)

    assert isinstance(formatted, str)
    assert len(formatted) > 0
    assert "Test recommendation 1" in formatted
    assert "Test recommendation 2" in formatted
    assert "high" in formatted
    assert "medium" in formatted


def test_format_recommendations_empty(summarizer: ContextSummarizer) -> None:
    """Test recommendations formatting with empty list."""
    formatted = summarizer._format_recommendations([])
    assert formatted == ""


def test_generate_simple_summary(
    summarizer: ContextSummarizer,
    sample_merged_findings: list[dict[str, object]],
    sample_merged_risks: list[dict[str, object]],
    sample_merged_recommendations: list[dict[str, object]],
) -> None:
    """Test simple summary generation."""
    summary = summarizer.generate_simple_summary(
        merged_findings=sample_merged_findings,
        merged_risks=sample_merged_risks,
        merged_recommendations=sample_merged_recommendations,
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "Historical analyses" in summary or "findings" in summary.lower()
    assert "risks" in summary.lower()
    assert "recommendations" in summary.lower()


def test_generate_simple_summary_empty(summarizer: ContextSummarizer) -> None:
    """Test simple summary generation with no results."""
    summary = summarizer.generate_simple_summary(
        merged_findings=[],
        merged_risks=[],
        merged_recommendations=[],
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "No relevant historical context" in summary


def test_generate_simple_summary_findings_only(
    summarizer: ContextSummarizer,
    sample_merged_findings: list[dict[str, object]],
) -> None:
    """Test simple summary with only findings."""
    summary = summarizer.generate_simple_summary(
        merged_findings=sample_merged_findings,
        merged_risks=[],
        merged_recommendations=[],
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "findings" in summary.lower() or "analyses" in summary.lower()


def test_generate_simple_summary_limits_results(
    summarizer: ContextSummarizer,
) -> None:
    """Test that simple summary limits the number of results."""
    many_findings = [
        {"content": f"Finding {i}", "category": "test"} for i in range(10)
    ]
    many_risks = [
        {"description": f"Risk {i}", "severity": "medium"} for i in range(10)
    ]
    many_recommendations = [
        {"content": f"Recommendation {i}", "priority": "low"} for i in range(10)
    ]

    summary = summarizer.generate_simple_summary(
        merged_findings=many_findings,
        merged_risks=many_risks,
        merged_recommendations=many_recommendations,
    )

    # Should limit to top 3 findings, 2 risks, 2 recommendations
    assert summary.count("Finding") <= 3 or summary.count(";") <= 7
