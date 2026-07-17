"""GraphRAG engine for unified graph and vector retrieval."""

from __future__ import annotations

from typing import Any

from loguru import logger

from graph.query_engine import GraphQueryEngine
from rag.context_fusion import ContextFusionEngine
from rag.context_summarizer import ContextSummarizer
from rag.query_engine import SemanticQueryEngine
from superagent.context_models import GraphRAGContext


class GraphRAGEngine:
    """Coordinate graph and vector retrieval for unified context generation."""

    def __init__(
        self,
        graph_query_engine: GraphQueryEngine | None = None,
        semantic_query_engine: SemanticQueryEngine | None = None,
    ) -> None:
        """Initialize the GraphRAG engine.

        Args:
            graph_query_engine: Engine for graph retrieval.
            semantic_query_engine: Engine for vector retrieval.
        """
        self.graph_query_engine = graph_query_engine
        self.semantic_query_engine = semantic_query_engine or SemanticQueryEngine()
        self.fusion_engine = ContextFusionEngine()
        self.summarizer = ContextSummarizer()

    def retrieve_context(self, query: str) -> GraphRAGContext:
        """Retrieve unified GraphRAG context for a query.

        Args:
            query: The user query.

        Returns:
            GraphRAGContext with merged graph and vector results.
        """
        logger.info("GraphRAG retrieval started for query: {}", query)

        retrieval_metadata: dict[str, Any] = {
            "graph_tasks": 0,
            "graph_findings": 0,
            "vector_documents": 0,
            "fusion_results": 0,
            "graph_available": False,
            "vector_available": False,
        }

        # Step 1: Graph Retrieval
        graph_results: list[dict[str, Any]] = []
        graph_findings: list[dict[str, Any]] = []
        graph_risks: list[dict[str, Any]] = []
        graph_recommendations: list[dict[str, Any]] = []

        try:
            if self.graph_query_engine:
                graph_context = self.graph_query_engine.build_graph_context(query)
                graph_results = graph_context.related_tasks
                graph_findings = graph_context.related_findings
                graph_risks = graph_context.related_risks
                graph_recommendations = graph_context.related_recommendations

                retrieval_metadata["graph_tasks"] = len(graph_results)
                retrieval_metadata["graph_findings"] = (
                    len(graph_findings) + len(graph_risks) + len(graph_recommendations)
                )
                retrieval_metadata["graph_available"] = True

                logger.info(
                    "Graph retrieval: {} tasks, {} findings, {} risks, {} recommendations",
                    len(graph_results),
                    len(graph_findings),
                    len(graph_risks),
                    len(graph_recommendations),
                )
        except Exception as exc:
            logger.warning("Graph retrieval failed: {}", exc)
            retrieval_metadata["graph_error"] = str(exc)

        # Step 2: Vector Retrieval
        vector_results: list[dict[str, Any]] = []
        vector_findings: list[dict[str, Any]] = []
        vector_risks: list[dict[str, Any]] = []
        vector_recommendations: list[dict[str, Any]] = []

        try:
            semantic_context = self.semantic_query_engine.build_semantic_context(query)
            vector_results = semantic_context.documents

            # Separate vector results by type
            for result in vector_results:
                metadata = result.get("metadata", {})
                source_type = metadata.get("source_type", "unknown")

                if source_type == "finding":
                    vector_findings.append(result)
                elif source_type == "risk":
                    vector_risks.append(result)
                elif source_type == "recommendation":
                    vector_recommendations.append(result)

            retrieval_metadata["vector_documents"] = len(vector_results)
            retrieval_metadata["vector_available"] = True

            logger.info(
                "Vector retrieval: {} total ({} findings, {} risks, {} recommendations)",
                len(vector_results),
                len(vector_findings),
                len(vector_risks),
                len(vector_recommendations),
            )
        except Exception as exc:
            logger.warning("Vector retrieval failed: {}", exc)
            retrieval_metadata["vector_error"] = str(exc)

        # Step 3: Fusion
        merged_results = self.fusion_engine.merge_results(
            graph_findings=graph_findings,
            vector_findings=vector_findings,
            graph_risks=graph_risks,
            vector_risks=vector_risks,
            graph_recommendations=graph_recommendations,
            vector_recommendations=vector_recommendations,
        )

        merged_findings = merged_results["findings"]
        merged_risks = merged_results["risks"]
        merged_recommendations = merged_results["recommendations"]

        retrieval_metadata["fusion_results"] = (
            len(merged_findings) + len(merged_risks) + len(merged_recommendations)
        )

        # Step 4: Context Summary
        context_summary = self.summarizer.generate_summary(
            query=query,
            graph_results=graph_results,
            vector_results=vector_results,
            merged_findings=merged_findings,
            merged_risks=merged_risks,
            merged_recommendations=merged_recommendations,
        )

        # Build GraphRAG context
        graphrag_context = GraphRAGContext(
            query=query,
            graph_results=graph_results,
            vector_results=vector_results,
            merged_findings=merged_findings,
            merged_risks=merged_risks,
            merged_recommendations=merged_recommendations,
            context_summary=context_summary,
            retrieval_metadata=retrieval_metadata,
        )

        logger.info("GraphRAG context generation complete")
        return graphrag_context

    def get_simple_context_summary(self, query: str) -> str:
        """Get a simple context summary without full GraphRAG context.

        Args:
            query: The user query.

        Returns:
            Simple summary string.
        """
        try:
            graphrag_context = self.retrieve_context(query)
            return self.summarizer.generate_simple_summary(
                merged_findings=graphrag_context.merged_findings,
                merged_risks=graphrag_context.merged_risks,
                merged_recommendations=graphrag_context.merged_recommendations,
            )
        except Exception as exc:
            logger.error("Failed to generate simple context summary: {}", exc)
            return "Context retrieval failed. Proceeding without historical context."

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the GraphRAG system.

        Returns:
            Dictionary with system statistics.
        """
        stats: dict[str, Any] = {
            "graph_available": self.graph_query_engine is not None,
            "vector_available": self.semantic_query_engine is not None,
        }

        # Try to get graph stats
        if self.graph_query_engine:
            try:
                graph_stats = self.graph_query_engine.graph_manager.get_stats()
                stats["graph_nodes"] = sum(graph_stats.values())
            except Exception as exc:
                logger.warning("Failed to get graph stats: {}", exc)
                stats["graph_nodes"] = 0

        # Try to get vector stats
        try:
            from rag.repository import VectorRepository

            vector_repo = VectorRepository()
            stats["vector_documents"] = vector_repo.count()
        except Exception as exc:
            logger.warning("Failed to get vector stats: {}", exc)
            stats["vector_documents"] = 0

        return stats
