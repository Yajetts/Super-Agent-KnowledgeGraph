"""Unit tests for agent GraphRAG integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.research_agent import ResearchAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from superagent.context_models import (
    Finding,
    GraphRAGContext,
    Recommendation,
    Risk,
    TaskContext,
)


@pytest.fixture
def mock_llm_service() -> MagicMock:
    """Create a mock LLM service."""
    service = MagicMock()
    service.generate = MagicMock(return_value='[{"category": "test", "content": "test finding", "confidence": 0.8}]')
    return service


@pytest.fixture
def sample_graphrag_context() -> GraphRAGContext:
    """Create a sample GraphRAG context."""
    return GraphRAGContext(
        query="EV market strategy",
        graph_results=[{"task_id": "task_1", "query": "EV market analysis"}],
        vector_results=[{"document_id": "doc_1", "content": "EV market growth"}],
        merged_findings=[
            {
                "content": "EV adoption is growing rapidly",
                "category": "market",
                "source": "graph",
                "combined_score": 0.9,
            }
        ],
        merged_risks=[
            {
                "description": "Policy uncertainty remains",
                "severity": "high",
                "source": "vector",
                "combined_score": 0.85,
            }
        ],
        merged_recommendations=[
            {
                "content": "Form strategic partnerships",
                "priority": "high",
                "source": "hybrid",
                "combined_score": 0.92,
            }
        ],
        context_summary="Historical analyses suggest EV adoption is growing rapidly. Related risks include policy uncertainty. Common recommendations include forming strategic partnerships.",
        retrieval_metadata={
            "graph_tasks": 1,
            "graph_findings": 1,
            "vector_documents": 1,
            "fusion_results": 3,
            "graph_available": True,
            "vector_available": True,
        },
    )


@pytest.fixture
def sample_task_context_with_graphrag(sample_graphrag_context: GraphRAGContext) -> TaskContext:
    """Create a sample task context with GraphRAG context."""
    return TaskContext(
        query="EV market strategy",
        task_type="business_analysis",
        graphrag_context=sample_graphrag_context,
    )


@pytest.fixture
def sample_task_context_without_graphrag() -> TaskContext:
    """Create a sample task context without GraphRAG context."""
    return TaskContext(
        query="EV market strategy",
        task_type="business_analysis",
    )


def test_research_agent_uses_graphrag_context(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that ResearchAgent uses GraphRAG context when available."""
    agent = ResearchAgent(llm_service=mock_llm_service)

    context = agent.execute(sample_task_context_with_graphrag)

    assert context.graphrag_context is not None
    assert agent.name in context.agent_history

    # Verify the LLM was called with GraphRAG context
    mock_llm_service.generate.assert_called_once()
    call_args = mock_llm_service.generate.call_args[0][0]
    assert "GraphRAG context summary" in call_args
    assert context.graphrag_context.context_summary in call_args


def test_research_agent_falls_back_to_no_context(
    mock_llm_service: MagicMock,
    sample_task_context_without_graphrag: TaskContext,
) -> None:
    """Test that ResearchAgent handles missing GraphRAG context gracefully."""
    agent = ResearchAgent(llm_service=mock_llm_service)

    context = agent.execute(sample_task_context_without_graphrag)

    assert context.graphrag_context is None
    assert agent.name in context.agent_history

    # Verify the LLM was called with fallback message
    mock_llm_service.generate.assert_called_once()
    call_args = mock_llm_service.generate.call_args[0][0]
    assert "No historical context available" in call_args


def test_risk_agent_uses_graphrag_context(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that RiskAgent uses GraphRAG context when available."""
    # Update mock to return risks
    mock_llm_service.generate.return_value = '[{"description": "test risk", "severity": "medium"}]'
    
    agent = RiskAgent(llm_service=mock_llm_service)
    
    # Add some findings for risk assessment
    sample_task_context_with_graphrag.findings = [
        Finding(
            source_agent="ResearchAgent",
            category="market",
            content="EV market is growing",
            confidence=0.9,
        )
    ]

    context = agent.execute(sample_task_context_with_graphrag)

    assert context.graphrag_context is not None
    assert agent.name in context.agent_history

    # Verify the LLM was called with GraphRAG context
    mock_llm_service.generate.assert_called_once()
    call_args = mock_llm_service.generate.call_args[0][0]
    assert "GraphRAG context summary" in call_args
    assert context.graphrag_context.context_summary in call_args


def test_risk_agent_falls_back_to_no_context(
    mock_llm_service: MagicMock,
    sample_task_context_without_graphrag: TaskContext,
) -> None:
    """Test that RiskAgent handles missing GraphRAG context gracefully."""
    mock_llm_service.generate.return_value = '[{"description": "test risk", "severity": "medium"}]'
    
    agent = RiskAgent(llm_service=mock_llm_service)
    
    sample_task_context_without_graphrag.findings = [
        Finding(
            source_agent="ResearchAgent",
            category="market",
            content="EV market is growing",
            confidence=0.9,
        )
    ]

    context = agent.execute(sample_task_context_without_graphrag)

    assert context.graphrag_context is None
    assert agent.name in context.agent_history

    # Verify the LLM was called with fallback message
    mock_llm_service.generate.assert_called_once()
    call_args = mock_llm_service.generate.call_args[0][0]
    assert "No historical context available" in call_args


def test_strategy_agent_uses_graphrag_context(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that StrategyAgent uses GraphRAG context when available."""
    # Update mock to return recommendations
    mock_llm_service.generate.return_value = '[{"content": "test recommendation", "priority": "high"}]'
    
    agent = StrategyAgent(llm_service=mock_llm_service)
    
    # Add findings and risks for strategy generation
    sample_task_context_with_graphrag.findings = [
        Finding(
            source_agent="ResearchAgent",
            category="market",
            content="EV market is growing",
            confidence=0.9,
        )
    ]
    sample_task_context_with_graphrag.risks = [
        Risk(
            source_agent="RiskAgent",
            description="Policy uncertainty",
            severity="high",
        )
    ]

    context = agent.execute(sample_task_context_with_graphrag)

    assert context.graphrag_context is not None
    assert agent.name in context.agent_history

    # Verify the LLM was called with GraphRAG context
    mock_llm_service.generate.assert_called_once()
    call_args = mock_llm_service.generate.call_args[0][0]
    assert "GraphRAG context summary" in call_args
    assert context.graphrag_context.context_summary in call_args


def test_strategy_agent_falls_back_to_no_context(
    mock_llm_service: MagicMock,
    sample_task_context_without_graphrag: TaskContext,
) -> None:
    """Test that StrategyAgent handles missing GraphRAG context gracefully."""
    mock_llm_service.generate.return_value = '[{"content": "test recommendation", "priority": "high"}]'
    
    agent = StrategyAgent(llm_service=mock_llm_service)
    
    sample_task_context_without_graphrag.findings = [
        Finding(
            source_agent="ResearchAgent",
            category="market",
            content="EV market is growing",
            confidence=0.9,
        )
    ]
    sample_task_context_without_graphrag.risks = [
        Risk(
            source_agent="RiskAgent",
            description="Policy uncertainty",
            severity="high",
        )
    ]

    context = agent.execute(sample_task_context_without_graphrag)

    assert context.graphrag_context is None
    assert agent.name in context.agent_history

    # Verify the LLM was called with fallback message
    mock_llm_service.generate.assert_called_once()
    call_args = mock_llm_service.generate.call_args[0][0]
    assert "No historical context available" in call_args


def test_research_agent_prompt_includes_graphrag_description(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that ResearchAgent prompt includes GraphRAG description."""
    agent = ResearchAgent(llm_service=mock_llm_service)

    agent.execute(sample_task_context_with_graphrag)

    call_args = mock_llm_service.generate.call_args[0][0]
    assert "knowledge graph and semantic search" in call_args
    assert "structural relationships and semantic similarity" in call_args


def test_risk_agent_prompt_includes_graphrag_description(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that RiskAgent prompt includes GraphRAG description."""
    mock_llm_service.generate.return_value = '[{"description": "test risk", "severity": "medium"}]'
    
    agent = RiskAgent(llm_service=mock_llm_service)
    sample_task_context_with_graphrag.findings = [
        Finding(
            source_agent="ResearchAgent",
            category="market",
            content="EV market is growing",
            confidence=0.9,
        )
    ]

    agent.execute(sample_task_context_with_graphrag)

    call_args = mock_llm_service.generate.call_args[0][0]
    assert "knowledge graph and semantic search" in call_args
    assert "structural relationships and semantic similarity" in call_args


def test_strategy_agent_prompt_includes_graphrag_description(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that StrategyAgent prompt includes GraphRAG description."""
    mock_llm_service.generate.return_value = '[{"content": "test recommendation", "priority": "high"}]'
    
    agent = StrategyAgent(llm_service=mock_llm_service)
    sample_task_context_with_graphrag.findings = [
        Finding(
            source_agent="ResearchAgent",
            category="market",
            content="EV market is growing",
            confidence=0.9,
        )
    ]
    sample_task_context_with_graphrag.risks = [
        Risk(
            source_agent="RiskAgent",
            description="Policy uncertainty",
            severity="high",
        )
    ]

    agent.execute(sample_task_context_with_graphrag)

    call_args = mock_llm_service.generate.call_args[0][0]
    assert "knowledge graph and semantic search" in call_args
    assert "structural relationships and semantic similarity" in call_args


def test_agents_preserve_graphrag_context_after_execution(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that agents preserve GraphRAG context after execution."""
    mock_llm_service.generate.return_value = '[{"category": "test", "content": "test finding", "confidence": 0.8}]'
    
    research_agent = ResearchAgent(llm_service=mock_llm_service)
    context = research_agent.execute(sample_task_context_with_graphrag)

    assert context.graphrag_context is not None
    assert context.graphrag_context.query == "EV market strategy"


def test_agents_add_to_agent_history_with_graphrag(
    mock_llm_service: MagicMock,
    sample_task_context_with_graphrag: TaskContext,
) -> None:
    """Test that agents add themselves to agent history when using GraphRAG."""
    mock_llm_service.generate.return_value = '[{"category": "test", "content": "test finding", "confidence": 0.8}]'
    
    research_agent = ResearchAgent(llm_service=mock_llm_service)
    context = research_agent.execute(sample_task_context_with_graphrag)

    assert "ResearchAgent" in context.agent_history


def test_graphrag_context_includes_merged_results(
    sample_graphrag_context: GraphRAGContext,
) -> None:
    """Test that GraphRAG context includes merged results."""
    assert len(sample_graphrag_context.merged_findings) > 0
    assert len(sample_graphrag_context.merged_risks) > 0
    assert len(sample_graphrag_context.merged_recommendations) > 0


def test_graphrag_context_includes_retrieval_metadata(
    sample_graphrag_context: GraphRAGContext,
) -> None:
    """Test that GraphRAG context includes retrieval metadata."""
    assert sample_graphrag_context.retrieval_metadata is not None
    assert "graph_available" in sample_graphrag_context.retrieval_metadata
    assert "vector_available" in sample_graphrag_context.retrieval_metadata
