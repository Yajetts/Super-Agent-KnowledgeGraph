"""Vector repository providing a clean interface to ChromaDB."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from core.embedding_service import get_embedding_service
from rag.models import VectorDocument
from rag.vector_store import VectorStore

if TYPE_CHECKING:
    from collections.abc import Sequence


class VectorRepository:
    """Repository interface for vector database operations."""

    def __init__(self) -> None:
        """Initialize the vector repository."""
        self._vector_store = VectorStore()
        self._embedding_service = get_embedding_service()
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure the vector store is initialized."""
        if not self._initialized:
            self._vector_store.initialize()
            self._initialized = True

    def save_finding(
        self,
        document_id: str,
        content: str,
        source_agent: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Save a finding to the vector database.

        Args:
            document_id: Unique identifier for the document.
            content: Text content of the finding.
            source_agent: Agent that generated this finding.
            metadata: Additional metadata about the finding.
        """
        self._ensure_initialized()

        if metadata is None:
            metadata = {}

        metadata_with_type = {
            **metadata,
            "source_type": "finding",
            "source_agent": source_agent,
        }

        try:
            embedding = self._embedding_service.embed_text(content)
            self._vector_store.add_document(
                document_id=document_id,
                content=content,
                embedding=embedding,
                metadata=metadata_with_type,
            )
            logger.info("Saved finding {} to vector database", document_id)
        except Exception as exc:
            logger.error("Failed to save finding {}: {}", document_id, exc)
            raise

    def save_risk(
        self,
        document_id: str,
        content: str,
        source_agent: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Save a risk to the vector database.

        Args:
            document_id: Unique identifier for the document.
            content: Text content of the risk.
            source_agent: Agent that generated this risk.
            metadata: Additional metadata about the risk.
        """
        self._ensure_initialized()

        if metadata is None:
            metadata = {}

        metadata_with_type = {
            **metadata,
            "source_type": "risk",
            "source_agent": source_agent,
        }

        try:
            embedding = self._embedding_service.embed_text(content)
            self._vector_store.add_document(
                document_id=document_id,
                content=content,
                embedding=embedding,
                metadata=metadata_with_type,
            )
            logger.info("Saved risk {} to vector database", document_id)
        except Exception as exc:
            logger.error("Failed to save risk {}: {}", document_id, exc)
            raise

    def save_recommendation(
        self,
        document_id: str,
        content: str,
        source_agent: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Save a recommendation to the vector database.

        Args:
            document_id: Unique identifier for the document.
            content: Text content of the recommendation.
            source_agent: Agent that generated this recommendation.
            metadata: Additional metadata about the recommendation.
        """
        self._ensure_initialized()

        if metadata is None:
            metadata = {}

        metadata_with_type = {
            **metadata,
            "source_type": "recommendation",
            "source_agent": source_agent,
        }

        try:
            embedding = self._embedding_service.embed_text(content)
            self._vector_store.add_document(
                document_id=document_id,
                content=content,
                embedding=embedding,
                metadata=metadata_with_type,
            )
            logger.info("Saved recommendation {} to vector database", document_id)
        except Exception as exc:
            logger.error("Failed to save recommendation {}: {}", document_id, exc)
            raise

    def save_documents(self, documents: Sequence[VectorDocument]) -> None:
        """Save multiple documents to the vector database.

        Args:
            documents: List of VectorDocument objects to save.
        """
        self._ensure_initialized()

        if not documents:
            logger.warning("No documents to save")
            return

        try:
            document_ids = [doc.document_id for doc in documents]
            contents = [doc.content for doc in documents]
            embeddings = self._embedding_service.embed_documents(contents)
            metadatas = [
                {
                    **doc.metadata,
                    "source_type": doc.source_type,
                    "source_agent": doc.source_agent,
                }
                for doc in documents
            ]

            self._vector_store.add_documents(
                document_ids=document_ids,
                contents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info("Saved {} documents to vector database", len(documents))
        except Exception as exc:
            logger.error("Failed to save documents: {}", exc)
            raise

    def semantic_search(
        self,
        query: str,
        n_results: int = 5,
        source_type: str | None = None,
    ) -> list[dict[str, object]]:
        """Perform semantic search on the vector database.

        Args:
            query: Search query text.
            n_results: Number of results to return.
            source_type: Optional filter by source type (finding, risk, recommendation).

        Returns:
            List of search results with document content, metadata, and similarity scores.
        """
        self._ensure_initialized()

        try:
            query_embedding = self._embedding_service.embed_text(query)
            where = {"source_type": source_type} if source_type else None
            results = self._vector_store.search(
                query_embedding=query_embedding,
                n_results=n_results,
                where=where,
            )

            formatted_results = []
            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            documents = results.get("documents", [[]])[0]

            for i, doc_id in enumerate(ids):
                formatted_results.append({
                    "document_id": doc_id,
                    "content": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "similarity_score": 1 - distances[i] if i < len(distances) else 0.0,
                })

            logger.info("Semantic search returned {} results for query: '{}'", len(formatted_results), query)
            return formatted_results
        except Exception as exc:
            logger.error("Failed to perform semantic search: {}", exc)
            raise

    def count(self) -> int:
        """Return the total number of documents in the vector database.

        Returns:
            Number of documents.
        """
        self._ensure_initialized()
        return self._vector_store.count()
