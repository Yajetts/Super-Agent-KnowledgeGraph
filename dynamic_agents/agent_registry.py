"""Upgraded agent registry with support for dynamic agents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from agents.agent_metadata import AGENT_METADATA, AgentMetadata
from dynamic_agents.models import AgentProfile
from dynamic_agents.repository import DynamicAgentRepository


class DynamicAgentRegistry:
    """Registry for both static and dynamic agents with enhanced metadata."""

    def __init__(self, repository: DynamicAgentRepository | None = None) -> None:
        """Initialize the dynamic agent registry.

        Args:
            repository: Repository for dynamic agent persistence. If None, creates default.
        """
        self.repository = repository or DynamicAgentRepository()
        self._dynamic_agents: dict[str, AgentProfile] = {}
        self._load_dynamic_agents()

    def _load_dynamic_agents(self) -> None:
        """Load dynamic agents from the repository on initialization."""
        try:
            dynamic_agents = self.repository.get_all_agents()
            for agent_record in dynamic_agents:
                profile = self._record_to_profile(agent_record)
                self._dynamic_agents[profile.name] = profile
            logger.info("Loaded {} dynamic agents from repository", len(self._dynamic_agents))
        except Exception as exc:
            logger.warning("Failed to load dynamic agents: {}", exc)

    def get_all_agents(self) -> list[dict[str, Any]]:
        """Return all registered agents (static and dynamic).

        Returns:
            List of agent dictionaries with metadata.
        """
        agents = []

        # Add static agents
        for name, metadata in AGENT_METADATA.items():
            agents.append(
                {
                    "name": name,
                    "description": metadata.description,
                    "skills": metadata.skills,
                    "task_types": [],  # Static agents don't have explicit task types
                    "creation_source": "static",
                    "creation_timestamp": None,
                    "usage_count": 0,
                    "is_dynamic": False,
                }
            )

        # Add dynamic agents
        for profile in self._dynamic_agents.values():
            agents.append(
                {
                    "name": profile.name,
                    "description": profile.description,
                    "skills": profile.skills,
                    "task_types": profile.supported_task_types,
                    "creation_source": profile.creation_source,
                    "creation_timestamp": profile.created_at.isoformat(),
                    "usage_count": profile.usage_count,
                    "last_used": profile.last_used.isoformat() if profile.last_used else None,
                    "success_score": profile.success_score,
                    "relevance_score": profile.relevance_score,
                    "is_dynamic": profile.is_dynamic,
                }
            )

        return agents

    def get_dynamic_agents(self) -> list[dict[str, Any]]:
        """Return only dynamic agents.

        Returns:
            List of dynamic agent dictionaries.
        """
        return [
            {
                "name": profile.name,
                "description": profile.description,
                "skills": profile.skills,
                "task_types": profile.supported_task_types,
                "creation_source": profile.creation_source,
                "creation_timestamp": profile.created_at.isoformat(),
                "usage_count": profile.usage_count,
                "last_used": profile.last_used.isoformat() if profile.last_used else None,
                "success_score": profile.success_score,
                "relevance_score": profile.relevance_score,
                "is_dynamic": profile.is_dynamic,
            }
            for profile in self._dynamic_agents.values()
        ]

    def get_agent_by_name(self, name: str) -> dict[str, Any] | None:
        """Return an agent by name (static or dynamic).

        Args:
            name: Name of the agent to retrieve.

        Returns:
            Agent dictionary if found, None otherwise.
        """
        # Check static agents first
        if name in AGENT_METADATA:
            metadata = AGENT_METADATA[name]
            return {
                "name": name,
                "description": metadata.description,
                "skills": metadata.skills,
                "task_types": [],
                "creation_source": "static",
                "creation_timestamp": None,
                "usage_count": 0,
                "is_dynamic": False,
            }

        # Check dynamic agents
        if name in self._dynamic_agents:
            profile = self._dynamic_agents[name]
            return {
                "name": profile.name,
                "description": profile.description,
                "skills": profile.skills,
                "task_types": profile.supported_task_types,
                "creation_source": profile.creation_source,
                "creation_timestamp": profile.created_at.isoformat(),
                "usage_count": profile.usage_count,
                "last_used": profile.last_used.isoformat() if profile.last_used else None,
                "success_score": profile.success_score,
                "relevance_score": profile.relevance_score,
                "is_dynamic": profile.is_dynamic,
            }

        return None

    def find_agents_by_skill(self, skill: str) -> list[dict[str, Any]]:
        """Return agents that possess a given skill.

        Args:
            skill: Skill to search for.

        Returns:
            List of agent dictionaries with the specified skill.
        """
        agents = []

        # Check static agents
        for name, metadata in AGENT_METADATA.items():
            if skill in metadata.skills:
                agents.append(
                    {
                        "name": name,
                        "description": metadata.description,
                        "skills": metadata.skills,
                        "task_types": [],
                        "creation_source": "static",
                        "creation_timestamp": None,
                        "usage_count": 0,
                        "is_dynamic": False,
                    }
                )

        # Check dynamic agents
        for profile in self._dynamic_agents.values():
            if skill in profile.skills:
                agents.append(
                    {
                        "name": profile.name,
                        "description": profile.description,
                        "skills": profile.skills,
                        "task_types": profile.supported_task_types,
                        "creation_source": profile.creation_source,
                        "creation_timestamp": profile.created_at.isoformat(),
                        "usage_count": profile.usage_count,
                        "last_used": profile.last_used.isoformat() if profile.last_used else None,
                        "success_score": profile.success_score,
                        "relevance_score": profile.relevance_score,
                        "is_dynamic": profile.is_dynamic,
                    }
                )

        return agents

    def find_agents_by_task_type(self, task_type: str) -> list[dict[str, Any]]:
        """Return agents that support a given task type.

        Args:
            task_type: Task type to search for.

        Returns:
            List of agent dictionaries supporting the task type.
        """
        agents = []

        # Dynamic agents have explicit task types
        for profile in self._dynamic_agents.values():
            if task_type in profile.supported_task_types:
                agents.append(
                    {
                        "name": profile.name,
                        "description": profile.description,
                        "skills": profile.skills,
                        "task_types": profile.supported_task_types,
                        "creation_source": profile.creation_source,
                        "creation_timestamp": profile.created_at.isoformat(),
                        "usage_count": profile.usage_count,
                        "last_used": profile.last_used.isoformat() if profile.last_used else None,
                        "success_score": profile.success_score,
                        "relevance_score": profile.relevance_score,
                        "is_dynamic": profile.is_dynamic,
                    }
                )

        return agents

    def register_agent(self, profile: AgentProfile) -> bool:
        """Register a new dynamic agent.

        Args:
            profile: Agent profile to register.

        Returns:
            True if registration was successful, False otherwise.
        """
        # Check for duplicates
        if profile.name in self._dynamic_agents or profile.name in AGENT_METADATA:
            logger.warning("Agent {} already exists, skipping registration", profile.name)
            return False

        # Add to in-memory registry
        self._dynamic_agents[profile.name] = profile

        # Persist to repository
        try:
            self.repository.save_agent(profile)
            logger.info("Successfully registered dynamic agent: {}", profile.name)
            return True
        except Exception as exc:
            logger.error("Failed to persist agent {}: {}", profile.name, exc)
            # Still keep in memory even if persistence fails
            return True

    def update_usage_count(self, agent_name: str) -> bool:
        """Increment the usage count for an agent.

        Args:
            agent_name: Name of the agent to update.

        Returns:
            True if update was successful, False otherwise.
        """
        # Update in-memory profile
        if agent_name in self._dynamic_agents:
            self._dynamic_agents[agent_name].usage_count += 1

            # Update in repository
            try:
                self.repository.update_usage(agent_name)
                logger.debug("Updated usage count for agent: {}", agent_name)
                return True
            except Exception as exc:
                logger.error("Failed to update usage count for {}: {}", agent_name, exc)
                return False

        return False

    def agent_exists(self, agent_name: str) -> bool:
        """Check if an agent exists (static or dynamic).

        Args:
            agent_name: Name of the agent to check.

        Returns:
            True if agent exists, False otherwise.
        """
        return agent_name in AGENT_METADATA or agent_name in self._dynamic_agents

    def get_agent_profile(self, agent_name: str) -> AgentProfile | None:
        """Get the full AgentProfile for a dynamic agent.

        Args:
            agent_name: Name of the agent.

        Returns:
            AgentProfile if found and dynamic, None otherwise.
        """
        return self._dynamic_agents.get(agent_name)

    def _record_to_profile(self, record: Any) -> AgentProfile:
        """Convert a database record to an AgentProfile.

        Args:
            record: Database record from DynamicAgentRecord.

        Returns:
            AgentProfile instance.
        """
        import json

        return AgentProfile(
            agent_id=str(record.id),
            name=record.name,
            description=record.description,
            skills=json.loads(record.skills) if record.skills else [],
            supported_task_types=[],  # Task types not stored in DB currently
            creation_source="dynamic",
            usage_count=record.usage_count,
            created_at=record.created_at,
            last_used=record.last_used,
            success_score=getattr(record, 'success_score', 1.0),
            relevance_score=getattr(record, 'relevance_score', 1.0),
            is_dynamic=True,
        )
