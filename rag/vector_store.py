"""Vector store implementation using ChromaDB for semantic retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from chromadb import Collection, HttpClient, PersistentClient
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from config.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import Sequence


class VectorStore:
    """Wrapper around ChromaDB for vector storage and retrieval."""

    def __init__(self) -> None:
        """Initialize the vector store."""
        self._client: PersistentClient | HttpClient | None = None
        self._collection: Collection | None = None
        self._initialized = False

    def initialize(self, collection_name: str = "documents") -> None:
        """Initialize the ChromaDB client and get or create collection.

        Args:
            collection_name: Name of the collection to use.
        """
        if self._initialized:
            logger.debug("VectorStore already initialized")
            return

        settings = get_settings()
        db_path = settings.chroma_db_path

        try:
            Path(db_path).mkdir(parents=True, exist_ok=True)
            self._client = PersistentClient(
                path=db_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._initialized = True
            logger.info("VectorStore initialized with collection: {}", collection_name)
        except Exception as exc:
            logger.error("Failed to initialize VectorStore: {}", exc)
            raise RuntimeError(f"VectorStore initialization failed: {exc}") from exc

    def add_document(
        self,
        document_id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, str],
    ) -> None:
        """Add a single document to the vector store.

        Args:
            document_id: Unique identifier for the document.
            content: Text content of the document.
            embedding: Embedding vector for the content.
            metadata: Additional metadata about the document.

        Raises:
            RuntimeError: If the vector store is not initialized or add fails.
        """
        if not self._initialized or self._collection is None:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")

        try:
            self._collection.add(
                ids=[document_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
            )
            logger.debug("Added document {} to vector store", document_id)
        except Exception as exc:
            logger.error("Failed to add document {}: {}", document_id, exc)
            raise RuntimeError(f"Failed to add document: {exc}") from exc

    def add_documents(
        self,
        document_ids: Sequence[str],
        contents: Sequence[str],
        embeddings: Sequence[list[float]],
        metadatas: Sequence[dict[str, str]],
    ) -> None:
        """Add multiple documents to the vector store.

        Args:
            document_ids: List of unique identifiers for the documents.
            contents: List of text contents.
            embeddings: List of embedding vectors.
            metadatas: List of metadata dictionaries.

        Raises:
            RuntimeError: If the vector store is not initialized or add fails.
        """
        if not self._initialized or self._collection is None:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")

        if len(document_ids) != len(contents) or len(contents) != len(embeddings):
            raise ValueError("All input sequences must have the same length.")

        try:
            self._collection.add(
                ids=list(document_ids),
                documents=list(contents),
                embeddings=list(embeddings),
                metadatas=list(metadatas),
            )
            logger.info("Added {} documents to vector store", len(document_ids))
        except Exception as exc:
            logger.error("Failed to add documents: {}", exc)
            raise RuntimeError(f"Failed to add documents: {exc}") from exc

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, str] | None = None,
    ) -> dict[str, list]:
        """Search for similar documents using a query embedding.

        Args:
            query_embedding: Embedding vector for the query.
            n_results: Number of results to return.
            where: Optional filter conditions on metadata.

        Returns:
            Dictionary containing search results with keys: ids, distances, metadatas, documents.

        Raises:
            RuntimeError: If the vector store is not initialized or search fails.
        """
        if not self._initialized or self._collection is None:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
            )
            logger.debug("Search returned {} results", len(results.get("ids", [[]])[0]))
            return results
        except Exception as exc:
            logger.error("Failed to search vector store: {}", exc)
            raise RuntimeError(f"Vector store search failed: {exc}") from exc

    def delete(self, document_ids: Sequence[str] | None = None) -> None:
        """Delete documents from the vector store.

        Args:
            document_ids: List of document IDs to delete. If None, deletes all.

        Raises:
            RuntimeError: If the vector store is not initialized or delete fails.
        """
        if not self._initialized or self._collection is None:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")

        try:
            if document_ids:
                self._collection.delete(ids=list(document_ids))
                logger.info("Deleted {} documents from vector store", len(document_ids))
            else:
                self._collection.delete(where={})
                logger.info("Deleted all documents from vector store")
        except Exception as exc:
            logger.error("Failed to delete documents: {}", exc)
            raise RuntimeError(f"Failed to delete documents: {exc}") from exc

    def count(self) -> int:
        """Return the total number of documents in the vector store.

        Returns:
            Number of documents in the collection.

        Raises:
            RuntimeError: If the vector store is not initialized.
        """
        if not self._initialized or self._collection is None:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")

        try:
            count = self._collection.count()
            logger.debug("Vector store contains {} documents", count)
            return count
        except Exception as exc:
            logger.error("Failed to count documents: {}", exc)
            raise RuntimeError(f"Failed to count documents: {exc}") from exc
