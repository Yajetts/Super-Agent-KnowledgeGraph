"""Unit tests for VectorStore."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from rag.vector_store import VectorStore


@pytest.fixture
def temp_vector_store() -> VectorStore:
    """Create a temporary vector store for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = VectorStore()
        # Monkey patch the initialization to use temp directory
        original_init = store.initialize

        def temp_init(collection_name: str = "documents") -> None:
            from chromadb import PersistentClient
            from chromadb.config import Settings as ChromaSettings

            Path(temp_dir).mkdir(parents=True, exist_ok=True)
            store._client = PersistentClient(
                path=temp_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            store._collection = store._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            store._initialized = True

        store.initialize = temp_init
        store.initialize()
        yield store
        # Cleanup
        if store._collection is not None:
            store._collection.delete(where={})


def test_vector_store_initialization(temp_vector_store: VectorStore) -> None:
    """Test that vector store initializes correctly."""
    assert temp_vector_store._initialized is True
    assert temp_vector_store._collection is not None


def test_vector_store_add_document(temp_vector_store: VectorStore) -> None:
    """Test adding a single document to the vector store."""
    document_id = "test_doc_1"
    content = "This is a test document about semantic search."
    embedding = [0.1] * 1536  # Mock embedding
    metadata = {"source_type": "finding", "source_agent": "test_agent"}

    temp_vector_store.add_document(document_id, content, embedding, metadata)

    count = temp_vector_store.count()
    assert count == 1


def test_vector_store_add_documents(temp_vector_store: VectorStore) -> None:
    """Test adding multiple documents to the vector store."""
    document_ids = ["doc_1", "doc_2", "doc_3"]
    contents = [
        "First document about electric vehicles.",
        "Second document about market expansion.",
        "Third document about strategic planning.",
    ]
    embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
    metadatas = [
        {"source_type": "finding", "source_agent": "agent1"},
        {"source_type": "risk", "source_agent": "agent2"},
        {"source_type": "recommendation", "source_agent": "agent3"},
    ]

    temp_vector_store.add_documents(document_ids, contents, embeddings, metadatas)

    count = temp_vector_store.count()
    assert count == 3


def test_vector_store_search(temp_vector_store: VectorStore) -> None:
    """Test searching the vector store."""
    # Add documents first
    document_ids = ["doc_1", "doc_2"]
    contents = [
        "Electric vehicle market is growing rapidly in India.",
        "Strategic expansion requires careful planning.",
    ]
    embeddings = [[0.1] * 1536, [0.2] * 1536]
    metadatas = [
        {"source_type": "finding", "source_agent": "agent1"},
        {"source_type": "recommendation", "source_agent": "agent2"},
    ]

    temp_vector_store.add_documents(document_ids, contents, embeddings, metadatas)

    # Search
    query_embedding = [0.1] * 1536
    results = temp_vector_store.search(query_embedding, n_results=2)

    assert "ids" in results
    assert "distances" in results
    assert "metadatas" in results
    assert "documents" in results
    assert len(results["ids"][0]) == 2


def test_vector_store_delete(temp_vector_store: VectorStore) -> None:
    """Test deleting documents from the vector store."""
    # Add documents
    document_ids = ["doc_1", "doc_2"]
    contents = ["Document 1", "Document 2"]
    embeddings = [[0.1] * 1536, [0.2] * 1536]
    metadatas = [{"source_type": "finding"}, {"source_type": "risk"}]

    temp_vector_store.add_documents(document_ids, contents, embeddings, metadatas)

    # Delete one document
    temp_vector_store.delete(["doc_1"])

    count = temp_vector_store.count()
    assert count == 1


def test_vector_store_count(temp_vector_store: VectorStore) -> None:
    """Test counting documents in the vector store."""
    # Initially empty
    assert temp_vector_store.count() == 0

    # Add documents
    document_ids = ["doc_1", "doc_2", "doc_3"]
    contents = ["Doc 1", "Doc 2", "Doc 3"]
    embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
    metadatas = [{"source_type": "finding"}] * 3

    temp_vector_store.add_documents(document_ids, contents, embeddings, metadatas)

    # Count should be 3
    assert temp_vector_store.count() == 3


def test_vector_store_not_initialized_error() -> None:
    """Test that operations fail when vector store is not initialized."""
    store = VectorStore()

    with pytest.raises(RuntimeError, match="not initialized"):
        store.count()

    with pytest.raises(RuntimeError, match="not initialized"):
        store.add_document("id", "content", [0.1] * 1536, {})


def test_vector_store_search_with_filter(temp_vector_store: VectorStore) -> None:
    """Test searching with metadata filter."""
    # Add documents with different source types
    document_ids = ["doc_1", "doc_2", "doc_3"]
    contents = ["Finding about EV market", "Risk about expansion", "Recommendation for strategy"]
    embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
    metadatas = [
        {"source_type": "finding", "source_agent": "agent1"},
        {"source_type": "risk", "source_agent": "agent2"},
        {"source_type": "recommendation", "source_agent": "agent3"},
    ]

    temp_vector_store.add_documents(document_ids, contents, embeddings, metadatas)

    # Search with filter
    query_embedding = [0.1] * 1536
    results = temp_vector_store.search(query_embedding, n_results=5, where={"source_type": "finding"})

    # Should only return finding
    assert len(results["ids"][0]) == 1
    assert results["metadatas"][0][0]["source_type"] == "finding"
