"""Graph integration for dynamic agents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from dynamic_agents.models import AgentProfile
from graph.graph_manager import GraphManager


class DynamicAgentGraphIntegration:
    """Handles graph operations for dynamic agents."""

    def __init__(self, graph_manager: GraphManager | None = None) -> None:
        """Initialize the graph integration.

        Args:
            graph_manager: Graph manager instance. If None, creates default.
        """
        from graph.graph_manager import GraphManager

        self.graph_manager = graph_manager or GraphManager()

    def create_dynamic_agent_node(self, profile: AgentProfile) -> bool:
        """Create a graph node for a dynamic agent.

        Args:
            profile: Agent profile to create node for.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create the agent node with dynamic-specific properties
            self.graph_manager.create_agent_node(profile.name, profile.description)

            # Add dynamic agent properties
            query = """
            MATCH (agent:Agent {name: $name})
            SET agent.is_dynamic = $is_dynamic,
                agent.creation_source = $creation_source,
                agent.usage_count = $usage_count,
                agent.created_at = $created_at,
                agent.agent_id = $agent_id
            RETURN agent
            """
            self.graph_manager.run_write(
                query,
                {
                    "name": profile.name,
                    "is_dynamic": profile.is_dynamic,
                    "creation_source": profile.creation_source,
                    "usage_count": profile.usage_count,
                    "created_at": profile.created_at.isoformat(),
                    "agent_id": profile.agent_id,
                },
            )

            logger.info("Created dynamic agent node: {}", profile.name)
            return True

        except Exception as exc:
            logger.error("Failed to create dynamic agent node {}: {}", profile.name, exc)
            return False

    def create_skill_relationships(self, profile: AgentProfile) -> bool:
        """Create USES_SKILL relationships between agent and skills.

        Args:
            profile: Agent profile to create relationships for.

        Returns:
            True if successful, False otherwise.
        """
        try:
            for skill in profile.skills:
                # Create skill node if it doesn't exist
                self.graph_manager.create_skill_node(skill)

                # Create relationship
                self.graph_manager.create_relationship(
                    source_label="Agent",
                    source_properties={"name": profile.name},
                    relation_type="USES_SKILL",
                    target_label="Skill",
                    target_properties={"name": skill},
                )

            logger.info("Created skill relationships for agent: {}", profile.name)
            return True

        except Exception as exc:
            logger.error("Failed to create skill relationships for {}: {}", profile.name, exc)
            return False

    def create_task_relationship(
        self,
        agent_name: str,
        task_id: str,
        relationship_type: str = "CREATED_FOR_TASK",
    ) -> bool:
        """Create a relationship between agent and task.

        Args:
            agent_name: Name of the agent.
            task_id: ID of the task.
            relationship_type: Type of relationship to create.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self.graph_manager.create_relationship(
                source_label="Agent",
                source_properties={"name": agent_name},
                relation_type=relationship_type,
                target_label="Task",
                target_properties={"task_id": task_id},
                relationship_properties={"timestamp": datetime.utcnow().isoformat()},
            )

            logger.info("Created {} relationship for agent {} and task {}", relationship_type, agent_name, task_id)
            return True

        except Exception as exc:
            logger.error("Failed to create task relationship: {}", exc)
            return False

    def create_workflow_participation_relationship(
        self,
        agent_name: str,
        task_id: str,
    ) -> bool:
        """Create a PARTICIPATED_IN_WORKFLOW relationship.

        Args:
            agent_name: Name of the agent.
            task_id: ID of the task/workflow.

        Returns:
            True if successful, False otherwise.
        """
        return self.create_task_relationship(agent_name, task_id, "PARTICIPATED_IN_WORKFLOW")

    def update_agent_usage_count(self, agent_name: str, new_count: int) -> bool:
        """Update the usage count for an agent in the graph.

        Args:
            agent_name: Name of the agent.
            new_count: New usage count.

        Returns:
            True if successful, False otherwise.
        """
        try:
            query = """
            MATCH (agent:Agent {name: $name})
            SET agent.usage_count = $count
            RETURN agent
            """
            self.graph_manager.run_write(query, {"name": agent_name, "count": new_count})
            logger.debug("Updated usage count for agent {} to {}", agent_name, new_count)
            return True

        except Exception as exc:
            logger.error("Failed to update usage count for {}: {}", agent_name, exc)
            return False

    def get_dynamic_agent_stats(self) -> dict[str, Any]:
        """Get statistics about dynamic agents in the graph.

        Returns:
            Dictionary with dynamic agent statistics.
        """
        try:
            query = """
            MATCH (agent:Agent {is_dynamic: true})
            OPTIONAL MATCH (agent)-[r:USES_SKILL]->(skill:Skill)
            RETURN count(DISTINCT agent) as total_dynamic_agents,
                   count(DISTINCT skill) as total_skills,
                   sum(agent.usage_count) as total_usage
            """
            records = self.graph_manager.run_read(query)

            if records:
                record = records[0]
                return {
                    "total_dynamic_agents": record.get("total_dynamic_agents", 0),
                    "total_skills": record.get("total_skills", 0),
                    "total_usage": record.get("total_usage", 0),
                }

            return {"total_dynamic_agents": 0, "total_skills": 0, "total_usage": 0}

        except Exception as exc:
            logger.error("Failed to get dynamic agent stats: {}", exc)
            return {"total_dynamic_agents": 0, "total_skills": 0, "total_usage": 0}

    def register_agent_creation_event(
        self,
        profile: AgentProfile,
        task_query: str,
        task_type: str,
    ) -> bool:
        """Register the complete agent creation event in the graph.

        This creates:
        - The dynamic agent node
        - Skill relationships
        - Creation event metadata

        Args:
            profile: Agent profile being created.
            task_query: Task that triggered creation.
            task_type: Type of task.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create agent node
            self.create_dynamic_agent_node(profile)

            # Create skill relationships
            self.create_skill_relationships(profile)

            # Store creation context as a relationship property or separate node
            # For now, we'll add it as metadata to the agent node
            query = """
            MATCH (agent:Agent {name: $name})
            SET agent.creation_context = $context,
                agent.creation_task_type = $task_type
            RETURN agent
            """
            self.graph_manager.run_write(
                query,
                {
                    "name": profile.name,
                    "context": task_query,
                    "task_type": task_type,
                },
            )

            logger.info("Registered agent creation event for: {}", profile.name)
            return True

        except Exception as exc:
            logger.error("Failed to register agent creation event: {}", exc)
            return False
