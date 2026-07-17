"""Graph-enhanced retrieval placeholder implementation."""

from __future__ import annotations

from rag.retriever import Retriever


class GraphRAG:
    """Coordinate graph-enhanced retrieval operations in future phases."""

    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever

    def answer(self, query: str) -> str:
        """Provide an answer placeholder for a retrieval query."""
        raise NotImplementedError("GraphRAG.answer is not implemented yet.")
