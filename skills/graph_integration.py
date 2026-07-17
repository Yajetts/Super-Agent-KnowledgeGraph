"""Graph integration for skills."""

from __future__ import annotations

from typing import Any

from loguru import logger

from graph.graph_manager import GraphManager
from skills.models import Skill


class SkillGraphIntegration:
    """Handles graph operations for skills."""

    def __init__(self, graph_manager: GraphManager | None = None) -> None:
        """Initialize the skill graph integration.

        Args:
            graph_manager: Graph manager instance. If None, creates default.
        """
        self.graph_manager = graph_manager or GraphManager()

    def create_skill_node(
        self,
        skill_name: str,
        description: str,
        file_path: str,
    ) -> bool:
        """Create a graph node for a skill.

        Args:
            skill_name: Name of the skill.
            description: Description of the skill.
            file_path: Path to the skill markdown file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create the skill node
            query = """
            MERGE (skill:Skill {name: $name})
            SET skill.description = $description,
                skill.file_path = $file_path,
                skill.created_at = datetime()
            RETURN skill
            """
            self.graph_manager.run_write(
                query,
                {
                    "name": skill_name,
                    "description": description,
                    "file_path": file_path,
                },
            )

            logger.info("Created skill node: {}", skill_name)
            return True

        except Exception as exc:
            logger.error("Failed to create skill node {}: {}", skill_name, exc)
            return False

    def create_agent_skill_relationship(
        self,
        agent_name: str,
        skill_name: str,
    ) -> bool:
        """Create a HAS_SKILL relationship between agent and skill.

        Args:
            agent_name: Name of the agent.
            skill_name: Name of the skill.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create skill node if it doesn't exist
            self.graph_manager.create_skill_node(skill_name)

            # Create relationship
            query = """
            MATCH (agent:Agent {name: $agent_name})
            MATCH (skill:Skill {name: $skill_name})
            MERGE (agent)-[r:HAS_SKILL]->(skill)
            SET r.assigned_at = datetime()
            RETURN r
            """
            self.graph_manager.run_write(
                query,
                {
                    "agent_name": agent_name,
                    "skill_name": skill_name,
                },
            )

            logger.info("Created HAS_SKILL relationship: {} -> {}", agent_name, skill_name)
            return True

        except Exception as exc:
            logger.error("Failed to create HAS_SKILL relationship: {} -> {}: {}", agent_name, skill_name, exc)
            return False

    def get_agent_skills(self, agent_name: str) -> list[str]:
        """Get all skills assigned to an agent.

        Args:
            agent_name: Name of the agent.

        Returns:
            List of skill names.
        """
        try:
            query = """
            MATCH (agent:Agent {name: $agent_name})-[:HAS_SKILL]->(skill:Skill)
            RETURN skill.name as skill_name
            """
            records = self.graph_manager.run_read(query, {"agent_name": agent_name})
            return [record["skill_name"] for record in records]

        except Exception as exc:
            logger.error("Failed to get skills for agent {}: {}", agent_name, exc)
            return []

    def get_skill_agents(self, skill_name: str) -> list[str]:
        """Get all agents that have a specific skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            List of agent names.
        """
        try:
            query = """
            MATCH (agent:Agent)-[:HAS_SKILL]->(skill:Skill {name: $skill_name})
            RETURN agent.name as agent_name
            """
            records = self.graph_manager.run_read(query, {"skill_name": skill_name})
            return [record["agent_name"] for record in records]

        except Exception as exc:
            logger.error("Failed to get agents for skill {}: {}", skill_name, exc)
            return []

    def remove_agent_skill_relationship(
        self,
        agent_name: str,
        skill_name: str,
    ) -> bool:
        """Remove a HAS_SKILL relationship between agent and skill.

        Args:
            agent_name: Name of the agent.
            skill_name: Name of the skill.

        Returns:
            True if successful, False otherwise.
        """
        try:
            query = """
            MATCH (agent:Agent {name: $agent_name})-[r:HAS_SKILL]->(skill:Skill {name: $skill_name})
            DELETE r
            RETURN count(r) as deleted
            """
            self.graph_manager.run_write(
                query,
                {
                    "agent_name": agent_name,
                    "skill_name": skill_name,
                },
            )

            logger.info("Removed HAS_SKILL relationship: {} -> {}", agent_name, skill_name)
            return True

        except Exception as exc:
            logger.error("Failed to remove HAS_SKILL relationship: {} -> {}: {}", agent_name, skill_name, exc)
            return False

    def get_skill_stats(self) -> dict[str, Any]:
        """Get statistics about skills in the graph.

        Returns:
            Dictionary with skill statistics.
        """
        try:
            query = """
            MATCH (skill:Skill)
            OPTIONAL MATCH (agent:Agent)-[:HAS_SKILL]->(skill)
            RETURN count(DISTINCT skill) as total_skills,
                   count(DISTINCT agent) as total_agents_with_skills,
                   sum(size((agent)-[:HAS_SKILL]->(skill))) as total_relationships
            """
            records = self.graph_manager.run_read(query)

            if records:
                record = records[0]
                return {
                    "total_skills": record.get("total_skills", 0),
                    "total_agents_with_skills": record.get("total_agents_with_skills", 0),
                    "total_relationships": record.get("total_relationships", 0),
                }

            return {"total_skills": 0, "total_agents_with_skills": 0, "total_relationships": 0}

        except Exception as exc:
            logger.error("Failed to get skill stats: {}", exc)
            return {"total_skills": 0, "total_agents_with_skills": 0, "total_relationships": 0}

    def get_most_used_skills(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most frequently used skills.

        Args:
            limit: Maximum number of skills to return.

        Returns:
            List of skill names with usage counts.
        """
        try:
            query = """
            MATCH (agent:Agent)-[:HAS_SKILL]->(skill:Skill)
            RETURN skill.name as skill_name, count(agent) as usage_count
            ORDER BY usage_count DESC
            LIMIT $limit
            """
            records = self.graph_manager.run_read(query, {"limit": limit})
            return [{"skill_name": record["skill_name"], "usage_count": record["usage_count"]} for record in records]

        except Exception as exc:
            logger.error("Failed to get most used skills: {}", exc)
            return []
