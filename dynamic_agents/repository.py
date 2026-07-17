"""Repository for dynamic agent persistence in PostgreSQL."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from config.settings import get_settings
from dynamic_agents.models import AgentProfile, DynamicAgentRecord


class DynamicAgentRepository:
    """Repository for persisting and retrieving dynamic agents."""

    def __init__(self) -> None:
        """Initialize the repository with database connection."""
        self.settings = get_settings()
        self._engine = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize the database connection and create tables if needed."""
        try:
            db_url = (
                f"postgresql://{self.settings.postgres_user}:{self.settings.postgres_password}"
                f"@{self.settings.postgres_host}:{self.settings.postgres_port}/{self.settings.postgres_db}"
            )
            self._engine = create_engine(db_url)

            # Create tables if they don't exist
            DynamicAgentRecord.metadata.create_all(self._engine)

            logger.info("Dynamic agent repository initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize dynamic agent repository: {}", exc)
            raise RuntimeError(f"Database initialization failed: {exc}") from exc

    def _get_session(self) -> Session:
        """Get a database session.

        Returns:
            SQLAlchemy Session instance.
        """
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return Session(self._engine)

    def save_agent(self, profile: AgentProfile) -> bool:
        """Save a dynamic agent profile to the database.

        Args:
            profile: Agent profile to save.

        Returns:
            True if save was successful, False otherwise.
        """
        try:
            with self._get_session() as session:
                # Check if agent already exists
                existing = session.execute(
                    select(DynamicAgentRecord).where(DynamicAgentRecord.name == profile.name)
                ).scalar_one_or_none()

                if existing:
                    logger.warning("Agent {} already exists in database, updating", profile.name)
                    existing.description = profile.description
                    existing.skills = json.dumps(profile.skills)
                    existing.usage_count = profile.usage_count
                else:
                    # Create new record
                    record = DynamicAgentRecord(
                        name=profile.name,
                        description=profile.description,
                        skills=json.dumps(profile.skills),
                        system_prompt="",  # System prompt stored separately
                        usage_count=profile.usage_count,
                    )
                    session.add(record)

                session.commit()
                logger.info("Successfully saved agent: {}", profile.name)
                return True

        except Exception as exc:
            logger.error("Failed to save agent {}: {}", profile.name, exc)
            return False

    def get_agent(self, agent_name: str) -> DynamicAgentRecord | None:
        """Retrieve a dynamic agent by name.

        Args:
            agent_name: Name of the agent to retrieve.

        Returns:
            DynamicAgentRecord if found, None otherwise.
        """
        try:
            with self._get_session() as session:
                record = session.execute(
                    select(DynamicAgentRecord).where(DynamicAgentRecord.name == agent_name)
                ).scalar_one_or_none()
                return record
        except Exception as exc:
            logger.error("Failed to retrieve agent {}: {}", agent_name, exc)
            return None

    def get_all_agents(self) -> list[DynamicAgentRecord]:
        """Retrieve all dynamic agents from the database.

        Returns:
            List of DynamicAgentRecord objects.
        """
        try:
            with self._get_session() as session:
                records = session.execute(select(DynamicAgentRecord)).scalars().all()
                return list(records)
        except Exception as exc:
            logger.error("Failed to retrieve all agents: {}", exc)
            return []

    def update_usage(self, agent_name: str, success: bool = True) -> bool:
        """Increment the usage count and update lifecycle metrics for an agent.

        Args:
            agent_name: Name of the agent to update.
            success: Whether the agent execution was successful.

        Returns:
            True if update was successful, False otherwise.
        """
        try:
            with self._get_session() as session:
                record = session.execute(
                    select(DynamicAgentRecord).where(DynamicAgentRecord.name == agent_name)
                ).scalar_one_or_none()

                if record:
                    record.usage_count += 1
                    record.last_used = datetime.utcnow()

                    # Update success score using exponential moving average
                    if success:
                        # Weighted average: new score has 20% weight, historical has 80%
                        record.success_score = 0.8 * record.success_score + 0.2 * 1.0
                    else:
                        record.success_score = 0.8 * record.success_score + 0.2 * 0.0

                    session.commit()
                    logger.debug("Updated usage and lifecycle metrics for agent: {}", agent_name)
                    return True
                else:
                    logger.warning("Agent {} not found for usage update", agent_name)
                    return False

        except Exception as exc:
            logger.error("Failed to update usage for agent {}: {}", agent_name, exc)
            return False

    def update_relevance_score(self, agent_name: str, relevance_score: float) -> bool:
        """Update the relevance score for an agent.

        Args:
            agent_name: Name of the agent to update.
            relevance_score: New relevance score (0-1).

        Returns:
            True if update was successful, False otherwise.
        """
        try:
            with self._get_session() as session:
                record = session.execute(
                    select(DynamicAgentRecord).where(DynamicAgentRecord.name == agent_name)
                ).scalar_one_or_none()

                if record:
                    # Weighted average: new score has 30% weight, historical has 70%
                    record.relevance_score = 0.7 * record.relevance_score + 0.3 * relevance_score
                    session.commit()
                    logger.debug("Updated relevance score for agent: {} to {:.2f}", agent_name, record.relevance_score)
                    return True
                else:
                    logger.warning("Agent {} not found for relevance update", agent_name)
                    return False

        except Exception as exc:
            logger.error("Failed to update relevance score for agent {}: {}", agent_name, exc)
            return False

    def search_by_skill(self, skill: str) -> list[DynamicAgentRecord]:
        """Search for agents that have a specific skill.

        Args:
            skill: Skill to search for.

        Returns:
            List of DynamicAgentRecord objects with the specified skill.
        """
        try:
            with self._get_session() as session:
                records = session.execute(select(DynamicAgentRecord)).scalars().all()

                # Filter agents that have the skill
                matching_records = []
                for record in records:
                    try:
                        skills = json.loads(record.skills) if record.skills else []
                        if skill in skills:
                            matching_records.append(record)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse skills for agent {}", record.name)
                        continue

                return matching_records

        except Exception as exc:
            logger.error("Failed to search by skill {}: {}", skill, exc)
            return []

    def delete_agent(self, agent_name: str) -> bool:
        """Delete a dynamic agent from the database.

        Args:
            agent_name: Name of the agent to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            with self._get_session() as session:
                record = session.execute(
                    select(DynamicAgentRecord).where(DynamicAgentRecord.name == agent_name)
                ).scalar_one_or_none()

                if record:
                    session.delete(record)
                    session.commit()
                    logger.info("Successfully deleted agent: {}", agent_name)
                    return True
                else:
                    logger.warning("Agent {} not found for deletion", agent_name)
                    return False

        except Exception as exc:
            logger.error("Failed to delete agent {}: {}", agent_name, exc)
            return False

    def update_system_prompt(self, agent_name: str, system_prompt: str) -> bool:
        """Update the system prompt for an agent.

        Args:
            agent_name: Name of the agent to update.
            system_prompt: New system prompt.

        Returns:
            True if update was successful, False otherwise.
        """
        try:
            with self._get_session() as session:
                record = session.execute(
                    select(DynamicAgentRecord).where(DynamicAgentRecord.name == agent_name)
                ).scalar_one_or_none()

                if record:
                    record.system_prompt = system_prompt
                    session.commit()
                    logger.info("Successfully updated system prompt for agent: {}", agent_name)
                    return True
                else:
                    logger.warning("Agent {} not found for system prompt update", agent_name)
                    return False

        except Exception as exc:
            logger.error("Failed to update system prompt for agent {}: {}", agent_name, exc)
            return False

    def get_system_prompt(self, agent_name: str) -> str | None:
        """Retrieve the system prompt for an agent.

        Args:
            agent_name: Name of the agent.

        Returns:
            System prompt string if found, None otherwise.
        """
        try:
            with self._get_session() as session:
                record = session.execute(
                    select(DynamicAgentRecord).where(DynamicAgentRecord.name == agent_name)
                ).scalar_one_or_none()

                if record:
                    return record.system_prompt
                return None

        except Exception as exc:
            logger.error("Failed to retrieve system prompt for agent {}: {}", agent_name, exc)
            return None
