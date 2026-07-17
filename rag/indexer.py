"""Knowledge indexer for converting workflow outputs into vector documents."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from rag.models import VectorDocument
from rag.repository import VectorRepository

if TYPE_CHECKING:
    from superagent.schemas import WorkflowResult


class KnowledgeIndexer:
    """Index workflow outputs into the vector database automatically."""

    def __init__(self) -> None:
        """Initialize the knowledge indexer."""
        self._repository = VectorRepository()

    def index_workflow_result(self, result: WorkflowResult, task_id: str) -> None:
        """Convert and index workflow outputs into vector documents.

        Args:
            result: The workflow result containing findings, risks, and recommendations.
            task_id: The task ID associated with this workflow execution.
        """
        logger.info("Indexing workflow result for task: {}", task_id)

        documents: list[VectorDocument] = []

        # Index findings
        for i, finding in enumerate(result.findings):
            content = finding.content if hasattr(finding, "content") else str(finding)
            source_agent = finding.source_agent if hasattr(finding, "source_agent") else "research_agent"
            doc = VectorDocument(
                document_id=f"{task_id}_finding_{i}",
                content=content,
                source_type="finding",
                source_agent=source_agent,
                metadata={"task_id": task_id, "index": str(i)},
            )
            documents.append(doc)

        # Index risks
        for i, risk in enumerate(result.risks):
            content = risk.description if hasattr(risk, "description") else str(risk)
            source_agent = risk.source_agent if hasattr(risk, "source_agent") else "risk_agent"
            doc = VectorDocument(
                document_id=f"{task_id}_risk_{i}",
                content=content,
                source_type="risk",
                source_agent=source_agent,
                metadata={"task_id": task_id, "index": str(i)},
            )
            documents.append(doc)

        # Index recommendations
        for i, recommendation in enumerate(result.recommendations):
            content = recommendation.content if hasattr(recommendation, "content") else str(recommendation)
            source_agent = recommendation.source_agent if hasattr(recommendation, "source_agent") else "strategy_agent"
            doc = VectorDocument(
                document_id=f"{task_id}_recommendation_{i}",
                content=content,
                source_type="recommendation",
                source_agent=source_agent,
                metadata={"task_id": task_id, "index": str(i)},
            )
            documents.append(doc)

        if documents:
            try:
                self._repository.save_documents(documents)
                logger.info("Successfully indexed {} documents for task: {}", len(documents), task_id)
            except Exception as exc:
                logger.error("Failed to index documents for task {}: {}", task_id, exc)
                raise
        else:
            logger.warning("No documents to index for task: {}", task_id)

    def index_finding(
        self,
        task_id: str,
        finding: str,
        index: int,
        source_agent: str = "research_agent",
    ) -> None:
        """Index a single finding.

        Args:
            task_id: The task ID associated with this finding.
            finding: The finding text content.
            index: The index of this finding in the results.
            source_agent: The agent that generated this finding.
        """
        try:
            self._repository.save_finding(
                document_id=f"{task_id}_finding_{index}",
                content=finding,
                source_agent=source_agent,
                metadata={"task_id": task_id, "index": str(index)},
            )
            logger.debug("Indexed finding {} for task: {}", index, task_id)
        except Exception as exc:
            logger.error("Failed to index finding {} for task {}: {}", index, task_id, exc)
            raise

    def index_risk(
        self,
        task_id: str,
        risk: str,
        index: int,
        source_agent: str = "risk_agent",
    ) -> None:
        """Index a single risk.

        Args:
            task_id: The task ID associated with this risk.
            risk: The risk text content.
            index: The index of this risk in the results.
            source_agent: The agent that generated this risk.
        """
        try:
            self._repository.save_risk(
                document_id=f"{task_id}_risk_{index}",
                content=risk,
                source_agent=source_agent,
                metadata={"task_id": task_id, "index": str(index)},
            )
            logger.debug("Indexed risk {} for task: {}", index, task_id)
        except Exception as exc:
            logger.error("Failed to index risk {} for task {}: {}", index, task_id, exc)
            raise

    def index_recommendation(
        self,
        task_id: str,
        recommendation: str,
        index: int,
        source_agent: str = "strategy_agent",
    ) -> None:
        """Index a single recommendation.

        Args:
            task_id: The task ID associated with this recommendation.
            recommendation: The recommendation text content.
            index: The index of this recommendation in the results.
            source_agent: The agent that generated this recommendation.
        """
        try:
            self._repository.save_recommendation(
                document_id=f"{task_id}_recommendation_{index}",
                content=recommendation,
                source_agent=source_agent,
                metadata={"task_id": task_id, "index": str(index)},
            )
            logger.debug("Indexed recommendation {} for task: {}", index, task_id)
        except Exception as exc:
            logger.error("Failed to index recommendation {} for task {}: {}", index, task_id, exc)
            raise
