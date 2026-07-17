"""Retrieval abstraction for future vector and graph retrieval."""

from __future__ import annotations

from typing import Any


class Retriever:
    """Define the retrieval interface used by future RAG workflows."""

    def retrieve(self, query: str) -> list[Any]:
        """Return placeholder retrieval results for a query."""
        return []
