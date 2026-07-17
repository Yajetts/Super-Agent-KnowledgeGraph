"""Unit tests for KnowledgeIndexer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rag.indexer import KnowledgeIndexer
from rag.models import VectorDocument
from superagent.schemas import WorkflowResult


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock vector repository."""
    repo = MagicMock()
    repo.save_documents = MagicMock()
    repo.save_finding = MagicMock()
    repo.save_risk = MagicMock()
    repo.save_recommendation = MagicMock()
    return repo


@pytest.fixture
def indexer(mock_repository: MagicMock) -> KnowledgeIndexer:
    """Create a KnowledgeIndexer with mocked repository."""
    indexer = KnowledgeIndexer()
    indexer._repository = mock_repository
    return indexer


def test_index_workflow_result(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test indexing a complete workflow result."""
    result = WorkflowResult(
        query="Analyze EV market in India",
        findings=["EV adoption is growing rapidly", "Government incentives are available"],
        risks=["Infrastructure challenges", "High battery costs"],
        recommendations=["Focus on Tier-2 cities", "Partner with local manufacturers"],
        task_id="task-123",
    )

    indexer.index_workflow_result(result, "task-123")

    # Verify save_documents was called
    mock_repository.save_documents.assert_called_once()

    # Get the documents that were saved
    call_args = mock_repository.save_documents.call_args[0][0]
    assert len(call_args) == 4  # 2 findings + 2 risks + 2 recommendations = 6, but we have 2+2+2=6
    # Actually: 2 findings + 2 risks + 2 recommendations = 6 documents
    assert len(call_args) == 6

    # Verify document types
    source_types = [doc.source_type for doc in call_args]
    assert source_types.count("finding") == 2
    assert source_types.count("risk") == 2
    assert source_types.count("recommendation") == 2


def test_index_workflow_result_empty(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test indexing a workflow result with no data."""
    result = WorkflowResult(
        query="Empty query",
        findings=[],
        risks=[],
        recommendations=[],
        task_id="task-456",
    )

    indexer.index_workflow_result(result, "task-456")

    # Should not call save_documents with empty list
    mock_repository.save_documents.assert_not_called()


def test_index_finding(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test indexing a single finding."""
    indexer.index_finding("task-789", "EV market shows strong growth", 0, "research_agent")

    mock_repository.save_finding.assert_called_once_with(
        document_id="task-789_finding_0",
        content="EV market shows strong growth",
        source_agent="research_agent",
        metadata={"task_id": "task-789", "index": "0"},
    )


def test_index_risk(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test indexing a single risk."""
    indexer.index_risk("task-789", "Supply chain disruptions", 1, "risk_agent")

    mock_repository.save_risk.assert_called_once_with(
        document_id="task-789_risk_1",
        content="Supply chain disruptions",
        source_agent="risk_agent",
        metadata={"task_id": "task-789", "index": "1"},
    )


def test_index_recommendation(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test indexing a single recommendation."""
    indexer.index_recommendation("task-789", "Diversify supplier base", 2, "strategy_agent")

    mock_repository.save_recommendation.assert_called_once_with(
        document_id="task-789_recommendation_2",
        content="Diversify supplier base",
        source_agent="strategy_agent",
        metadata={"task_id": "task-789", "index": "2"},
    )


def test_index_multiple_findings(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test indexing multiple findings sequentially."""
    findings = ["Finding 1", "Finding 2", "Finding 3"]

    for i, finding in enumerate(findings):
        indexer.index_finding("task-multi", finding, i, "research_agent")

    assert mock_repository.save_finding.call_count == 3


def test_index_workflow_result_with_custom_agent(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test indexing with custom agent names."""
    result = WorkflowResult(
        query="Custom agent test",
        findings=["Custom finding"],
        risks=["Custom risk"],
        recommendations=["Custom recommendation"],
        task_id="task-custom",
    )

    indexer.index_workflow_result(result, "task-custom")

    call_args = mock_repository.save_documents.call_args[0][0]

    # Verify default agents are assigned
    agents = [doc.source_agent for doc in call_args]
    assert "research_agent" in agents
    assert "risk_agent" in agents
    assert "strategy_agent" in agents


def test_index_workflow_result_metadata(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test that metadata includes task_id and index."""
    result = WorkflowResult(
        query="Metadata test",
        findings=["Test finding"],
        risks=[],
        recommendations=[],
        task_id="task-meta-123",
    )

    indexer.index_workflow_result(result, "task-meta-123")

    call_args = mock_repository.save_documents.call_args[0][0]
    finding_doc = call_args[0]

    assert finding_doc.metadata["task_id"] == "task-meta-123"
    assert finding_doc.metadata["index"] == "0"


def test_index_workflow_result_handles_repository_error(indexer: KnowledgeIndexer, mock_repository: MagicMock) -> None:
    """Test that repository errors are propagated."""
    result = WorkflowResult(
        query="Error test",
        findings=["Test finding"],
        risks=[],
        recommendations=[],
        task_id="task-error",
    )

    mock_repository.save_documents.side_effect = RuntimeError("Database connection failed")

    with pytest.raises(RuntimeError, match="Database connection failed"):
        indexer.index_workflow_result(result, "task-error")
