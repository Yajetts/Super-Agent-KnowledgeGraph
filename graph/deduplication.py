"""Graph deduplication to prevent duplicate nodes in Neo4j."""

from __future__ import annotations

from typing import Any

from loguru import logger

from graph.graph_manager import GraphManager


class GraphDeduplicator:
    """Deduplicate graph nodes using semantic similarity."""

    def __init__(self, graph_manager: GraphManager | None = None) -> None:
        """Initialize the graph deduplicator.

        Args:
            graph_manager: Graph manager. If None, creates default.
        """
        self.graph_manager = graph_manager or GraphManager()

    def find_similar_findings(self, content: str, threshold: float = 0.85) -> list[dict[str, Any]]:
        """Find existing findings similar to the given content.

        Args:
            content: The finding content to check.
            threshold: Similarity threshold for matches.

        Returns:
            List of similar finding nodes.
        """
        query = """
        MATCH (f:Finding)
        WHERE f.content IS NOT NULL
        RETURN f.id as id, f.content as content, f.source_agent as source_agent
        """

        try:
            result = self.graph_manager.run_query(query)
            similar = []

            for record in result:
                existing_content = record.get("content", "")
                similarity = self._calculate_text_similarity(content, existing_content)

                if similarity >= threshold:
                    similar.append({
                        "id": record.get("id"),
                        "content": existing_content,
                        "source_agent": record.get("source_agent"),
                        "similarity": similarity,
                    })

            return similar
        except Exception as exc:
            logger.error("Failed to find similar findings: {}", exc)
            return []

    def find_similar_risks(self, description: str, threshold: float = 0.85) -> list[dict[str, Any]]:
        """Find existing risks similar to the given description.

        Args:
            description: The risk description to check.
            threshold: Similarity threshold for matches.

        Returns:
            List of similar risk nodes.
        """
        query = """
        MATCH (r:Risk)
        WHERE r.description IS NOT NULL
        RETURN r.id as id, r.description as description, r.source_agent as source_agent
        """

        try:
            result = self.graph_manager.run_query(query)
            similar = []

            for record in result:
                existing_desc = record.get("description", "")
                similarity = self._calculate_text_similarity(description, existing_desc)

                if similarity >= threshold:
                    similar.append({
                        "id": record.get("id"),
                        "description": existing_desc,
                        "source_agent": record.get("source_agent"),
                        "similarity": similarity,
                    })

            return similar
        except Exception as exc:
            logger.error("Failed to find similar risks: {}", exc)
            return []

    def find_similar_recommendations(self, content: str, threshold: float = 0.85) -> list[dict[str, Any]]:
        """Find existing recommendations similar to the given content.

        Args:
            content: The recommendation content to check.
            threshold: Similarity threshold for matches.

        Returns:
            List of similar recommendation nodes.
        """
        query = """
        MATCH (r:Recommendation)
        WHERE r.content IS NOT NULL
        RETURN r.id as id, r.content as content, r.source_agent as source_agent
        """

        try:
            result = self.graph_manager.run_query(query)
            similar = []

            for record in result:
                existing_content = record.get("content", "")
                similarity = self._calculate_text_similarity(content, existing_content)

                if similarity >= threshold:
                    similar.append({
                        "id": record.get("id"),
                        "content": existing_content,
                        "source_agent": record.get("source_agent"),
                        "similarity": similarity,
                    })

            return similar
        except Exception as exc:
            logger.error("Failed to find similar recommendations: {}", exc)
            return []

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using word overlap.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Similarity score between 0 and 1.
        """
        if not text1 or not text2:
            return 0.0

        # Tokenize and normalize
        words1 = set(word.lower() for word in text1.split() if len(word) > 3)
        words2 = set(word.lower() for word in text2.split() if len(word) > 3)

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def should_create_finding(self, content: str, threshold: float = 0.85) -> tuple[bool, dict[str, Any] | None]:
        """Determine if a new finding should be created or if an existing one should be reused.

        Args:
            content: The finding content.
            threshold: Similarity threshold for reuse.

        Returns:
            Tuple of (should_create, existing_node).
        """
        similar = self.find_similar_findings(content, threshold)

        if similar:
            best_match = similar[0]
            logger.info(
                "Reusing existing finding {} with similarity {:.2f}",
                best_match["id"],
                best_match["similarity"],
            )
            return False, best_match

        return True, None

    def should_create_risk(self, description: str, threshold: float = 0.85) -> tuple[bool, dict[str, Any] | None]:
        """Determine if a new risk should be created or if an existing one should be reused.

        Args:
            description: The risk description.
            threshold: Similarity threshold for reuse.

        Returns:
            Tuple of (should_create, existing_node).
        """
        similar = self.find_similar_risks(description, threshold)

        if similar:
            best_match = similar[0]
            logger.info(
                "Reusing existing risk {} with similarity {:.2f}",
                best_match["id"],
                best_match["similarity"],
            )
            return False, best_match

        return True, None

    def should_create_recommendation(self, content: str, threshold: float = 0.85) -> tuple[bool, dict[str, Any] | None]:
        """Determine if a new recommendation should be created or if an existing one should be reused.

        Args:
            content: The recommendation content.
            threshold: Similarity threshold for reuse.

        Returns:
            Tuple of (should_create, existing_node).
        """
        similar = self.find_similar_recommendations(content, threshold)

        if similar:
            best_match = similar[0]
            logger.info(
                "Reusing existing recommendation {} with similarity {:.2f}",
                best_match["id"],
                best_match["similarity"],
            )
            return False, best_match

        return True, None
