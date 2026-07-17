"""Context summarizer for generating concise summaries from retrieval results."""

from __future__ import annotations

from typing import Any

from loguru import logger


class ContextSummarizer:
    """Generate concise summaries from graph and vector retrieval results."""

    def generate_summary(
        self,
        query: str,
        graph_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        merged_findings: list[dict[str, Any]],
        merged_risks: list[dict[str, Any]],
        merged_recommendations: list[dict[str, Any]],
    ) -> str:
        """Generate a concise summary from retrieval results.

        Args:
            query: The original query.
            graph_results: Raw graph retrieval results.
            vector_results: Raw vector retrieval results.
            merged_findings: Merged and ranked findings.
            merged_risks: Merged and ranked risks.
            merged_recommendations: Merged and ranked recommendations.

        Returns:
            Concise summary string.
        """
        logger.info("Generating context summary for query: {}", query)

        summary_parts: list[str] = []

        # Add retrieval statistics
        graph_count = len(graph_results)
        vector_count = len(vector_results)
        if graph_count > 0 or vector_count > 0:
            summary_parts.append(
                f"Retrieved {graph_count} graph results and {vector_count} vector results."
            )

        # Add findings summary
        if merged_findings:
            top_findings = merged_findings[:3]
            findings_text = self._format_findings(top_findings)
            summary_parts.append(f"Key findings:\n{findings_text}")

        # Add risks summary
        if merged_risks:
            top_risks = merged_risks[:2]
            risks_text = self._format_risks(top_risks)
            summary_parts.append(f"Related risks:\n{risks_text}")

        # Add recommendations summary
        if merged_recommendations:
            top_recommendations = merged_recommendations[:2]
            recommendations_text = self._format_recommendations(top_recommendations)
            summary_parts.append(f"Common recommendations:\n{recommendations_text}")

        # Fallback if no results
        if not summary_parts:
            summary_parts.append(
                f"No relevant context found for query: '{query}'. "
                "Proceeding with fresh analysis."
            )

        summary = "\n\n".join(summary_parts)
        logger.info("Context summary generated")
        return summary

    def _format_findings(self, findings: list[dict[str, Any]]) -> str:
        """Format findings for summary.

        Args:
            findings: List of finding dictionaries.

        Returns:
            Formatted string of findings.
        """
        formatted = []
        for finding in findings:
            content = finding.get("content", "")
            category = finding.get("category", "general")
            source = finding.get("source", "unknown")
            score = finding.get("combined_score", 0)
            formatted.append(
                f"- [{category}] {content} (source: {source}, score: {score:.2f})"
            )
        return "\n".join(formatted)

    def _format_risks(self, risks: list[dict[str, Any]]) -> str:
        """Format risks for summary.

        Args:
            risks: List of risk dictionaries.

        Returns:
            Formatted string of risks.
        """
        formatted = []
        for risk in risks:
            description = risk.get("description", "")
            severity = risk.get("severity", "unknown")
            source = risk.get("source", "unknown")
            score = risk.get("combined_score", 0)
            formatted.append(
                f"- [{severity}] {description} (source: {source}, score: {score:.2f})"
            )
        return "\n".join(formatted)

    def _format_recommendations(self, recommendations: list[dict[str, Any]]) -> str:
        """Format recommendations for summary.

        Args:
            recommendations: List of recommendation dictionaries.

        Returns:
            Formatted string of recommendations.
        """
        formatted = []
        for recommendation in recommendations:
            content = recommendation.get("content", "")
            priority = recommendation.get("priority", "medium")
            source = recommendation.get("source", "unknown")
            score = recommendation.get("combined_score", 0)
            formatted.append(
                f"- [{priority}] {content} (source: {source}, score: {score:.2f})"
            )
        return "\n".join(formatted)

    def generate_simple_summary(
        self,
        merged_findings: list[dict[str, Any]],
        merged_risks: list[dict[str, Any]],
        merged_recommendations: list[dict[str, Any]],
    ) -> str:
        """Generate a simple summary without detailed metadata.

        Args:
            merged_findings: Merged and ranked findings.
            merged_risks: Merged and ranked risks.
            merged_recommendations: Merged and ranked recommendations.

        Returns:
            Simple summary string.
        """
        summary_parts: list[str] = []

        if merged_findings:
            top_findings = [str(f.get("content", "")).strip() for f in merged_findings[:3] if f.get("content")]
            if top_findings:
                summary_parts.append("Historical analyses suggest: " + "; ".join(top_findings))

        if merged_risks:
            top_risks = [str(r.get("description", "")).strip() for r in merged_risks[:2] if r.get("description")]
            if top_risks:
                summary_parts.append("Related risks: " + "; ".join(top_risks))

        if merged_recommendations:
            top_recommendations = [
                str(r.get("content", "")).strip() for r in merged_recommendations[:2] if r.get("content")
            ]
            if top_recommendations:
                summary_parts.append("Common recommendations: " + "; ".join(top_recommendations))

        if not summary_parts:
            return "No relevant historical context available."

        return "\n".join(summary_parts)
