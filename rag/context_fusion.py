"""Context fusion engine for merging graph and vector retrieval results."""

from __future__ import annotations

from typing import Any

from loguru import logger


class ContextFusionEngine:
    """Merge and rank retrieval results from graph and vector sources."""

    def __init__(self) -> None:
        """Initialize the context fusion engine."""
        self._graph_weight = 0.6
        self._vector_weight = 0.4

    def merge_results(
        self,
        graph_findings: list[dict[str, Any]],
        vector_findings: list[dict[str, Any]],
        graph_risks: list[dict[str, Any]],
        vector_risks: list[dict[str, Any]],
        graph_recommendations: list[dict[str, Any]],
        vector_recommendations: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Merge graph and vector retrieval results.

        Args:
            graph_findings: Findings from graph retrieval.
            vector_findings: Findings from vector retrieval.
            graph_risks: Risks from graph retrieval.
            vector_risks: Risks from vector retrieval.
            graph_recommendations: Recommendations from graph retrieval.
            vector_recommendations: Recommendations from vector retrieval.

        Returns:
            Dictionary with merged findings, risks, and recommendations.
        """
        logger.info("Merging graph and vector retrieval results")

        merged_findings = self._merge_and_deduplicate(
            graph_findings, vector_findings, "content"
        )
        merged_risks = self._merge_and_deduplicate(
            graph_risks, vector_risks, "description"
        )
        merged_recommendations = self._merge_and_deduplicate(
            graph_recommendations, vector_recommendations, "content"
        )

        logger.info(
            "Fusion complete: {} findings, {} risks, {} recommendations",
            len(merged_findings),
            len(merged_risks),
            len(merged_recommendations),
        )

        return {
            "findings": merged_findings,
            "risks": merged_risks,
            "recommendations": merged_recommendations,
        }

    def _merge_and_deduplicate(
        self,
        graph_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        content_field: str,
    ) -> list[dict[str, Any]]:
        """Merge and deduplicate results from two sources.

        Args:
            graph_results: Results from graph retrieval.
            vector_results: Results from vector retrieval.
            content_field: Field name to use for content comparison.

        Returns:
            Deduplicated and ranked list of results.
        """
        seen_content = set()
        merged_results = []

        # Process graph results first
        for result in graph_results:
            content = str(result.get(content_field, "")).strip().lower()
            if content and content not in seen_content:
                seen_content.add(content)
                result_copy = result.copy()
                result_copy["source"] = "graph"
                result_copy["combined_score"] = self._calculate_graph_score(result)
                merged_results.append(result_copy)

        # Process vector results
        for result in vector_results:
            content = str(result.get(content_field, "")).strip().lower()
            if content and content not in seen_content:
                seen_content.add(content)
                result_copy = result.copy()
                result_copy["source"] = "vector"
                result_copy["combined_score"] = self._calculate_vector_score(result)
                merged_results.append(result_copy)
            elif content:
                # Content already exists, update score if vector score is higher
                for existing in merged_results:
                    existing_content = str(existing.get(content_field, "")).strip().lower()
                    if existing_content == content:
                        vector_score = self._calculate_vector_score(result)
                        if vector_score > existing.get("combined_score", 0):
                            existing["combined_score"] = vector_score
                            existing["source"] = "hybrid"
                        break

        # Rank by combined score
        ranked_results = sorted(
            merged_results, key=lambda x: x.get("combined_score", 0), reverse=True
        )

        return ranked_results

    def _calculate_graph_score(self, result: dict[str, Any]) -> float:
        """Calculate score for graph-based result.

        Args:
            result: Graph retrieval result.

        Returns:
            Normalized score between 0 and 1.
        """
        score = 0.5  # Base score for graph results

        # Boost for confidence if available
        confidence = result.get("confidence")
        if confidence is not None:
            try:
                score += float(confidence) * 0.3
            except (ValueError, TypeError):
                pass

        # Boost for match score if available
        match_score = result.get("match_score")
        if match_score is not None:
            try:
                score += float(match_score) * 0.2
            except (ValueError, TypeError):
                pass

        return min(score, 1.0)

    def _calculate_vector_score(self, result: dict[str, Any]) -> float:
        """Calculate score for vector-based result.

        Args:
            result: Vector retrieval result.

        Returns:
            Normalized score between 0 and 1.
        """
        score = 0.0

        # Use similarity score if available
        similarity_score = result.get("similarity_score")
        if similarity_score is not None:
            try:
                score = float(similarity_score) * self._vector_weight
            except (ValueError, TypeError):
                score = 0.3
        else:
            score = 0.3

        return min(score, 1.0)

    def rank_by_confidence(
        self, results: list[dict[str, Any]], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Rank results by combined confidence score.

        Args:
            results: List of results to rank.
            limit: Maximum number of results to return.

        Returns:
            Ranked list of results.
        """
        ranked = sorted(
            results, key=lambda x: x.get("combined_score", 0), reverse=True
        )
        return ranked[:limit]
