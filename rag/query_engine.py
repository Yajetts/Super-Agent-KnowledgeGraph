"""Semantic query engine for vector-based retrieval."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from rag.models import SemanticContext
from rag.repository import VectorRepository

if TYPE_CHECKING:
    pass


class SemanticQueryEngine:
    """Engine for performing semantic searches and building context."""

    def __init__(self) -> None:
        """Initialize the semantic query engine."""
        self._repository = VectorRepository()

    def search(
        self,
        query: str,
        n_results: int = 5,
        source_type: str | None = None,
    ) -> SemanticContext:
        """Perform semantic search and return context.

        Args:
            query: The search query text.
            n_results: Number of results to return.
            source_type: Optional filter by source type (finding, risk, recommendation).

        Returns:
            SemanticContext containing documents, similarity scores, and summary.
        """
        logger.info("Performing semantic search for query: '{}'", query)

        try:
            results = self._repository.semantic_search(
                query=query,
                n_results=n_results,
                source_type=source_type,
            )

            similarity_scores = [result["similarity_score"] for result in results]
            documents = [result for result in results]

            summary = self._build_summary(query, results)

            context = SemanticContext(
                documents=documents,
                summary=summary,
                similarity_scores=similarity_scores,
            )

            logger.info("Semantic search completed with {} results", len(results))
            return context
        except Exception as exc:
            logger.error("Semantic search failed: {}", exc)
            raise

    def build_semantic_context(
        self,
        query: str,
        n_results: int = 5,
        source_types: list[str] | None = None,
    ) -> SemanticContext:
        """Build semantic context by searching across multiple source types.

        Args:
            query: The search query text.
            n_results: Number of results per source type.
            source_types: List of source types to search (finding, risk, recommendation).
                         If None, searches all types.

        Returns:
            SemanticContext containing aggregated results from all source types.
        """
        logger.info("Building semantic context for query: '{}'", query)

        if source_types is None:
            source_types = ["finding", "risk", "recommendation"]

        all_results: list[dict[str, object]] = []
        all_scores: list[float] = []

        for source_type in source_types:
            try:
                context = self.search(
                    query=query,
                    n_results=n_results,
                    source_type=source_type,
                )
                all_results.extend(context.documents)
                all_scores.extend(context.similarity_scores)
            except Exception as exc:
                logger.warning("Failed to search source type {}: {}", source_type, exc)
                continue

        # Sort by similarity score
        sorted_results = sorted(
            zip(all_results, all_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        top_results = [item[0] for item in sorted_results[:n_results]]
        top_scores = [item[1] for item in sorted_results[:n_results]]

        summary = self._build_summary(query, top_results)

        context = SemanticContext(
            documents=top_results,
            summary=summary,
            similarity_scores=top_scores,
        )

        logger.info("Built semantic context with {} documents", len(top_results))
        return context

    def _build_summary(self, query: str, results: list[dict[str, object]]) -> str:
        """Build a summary of the search results.

        Args:
            query: The original search query.
            results: List of search results.

        Returns:
            A summary string describing the results.
        """
        if not results:
            return f"No relevant documents found for query: '{query}'"

        source_types = set()
        for result in results:
            metadata = result.get("metadata", {})
            source_type = metadata.get("source_type", "unknown")
            source_types.add(source_type)

        type_str = ", ".join(sorted(source_types))
        return f"Found {len(results)} relevant documents from {type_str} for query: '{query}'"
