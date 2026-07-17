"""SkillManager for managing agent skills."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from config.settings import get_settings
from skills.graph_integration import SkillGraphIntegration
from skills.models import AgentSkill, Skill, SkillMetrics


class SkillManager:
    """Manages skill loading, assignment, and retrieval for agents."""

    # Task type to skill mapping
    TASK_TYPE_SKILL_MAPPING = {
        "risk_analysis": ["RiskAssessmentSkill", "RootCauseAnalysisSkill", "RecommendationSkill"],
        "strategy": ["StrategySkill", "SWOTSkill", "CostBenefitAnalysisSkill"],
        "analysis": ["ResearchSkill", "AnalysisSkill", "ForecastingSkill"],
        "compliance": ["ComplianceSkill", "RiskAssessmentSkill", "ResearchSkill"],
        "market_research": ["MarketAnalysisSkill", "ResearchSkill", "ForecastingSkill"],
        "research": ["ResearchSkill", "AnalysisSkill"],
        "planning": ["StrategySkill", "ForecastingSkill", "CostBenefitAnalysisSkill"],
        "evaluation": ["AnalysisSkill", "RecommendationSkill", "SWOTSkill"],
        "assessment": ["RiskAssessmentSkill", "AnalysisSkill", "RecommendationSkill"],
        "forecasting": ["ForecastingSkill", "AnalysisSkill", "ResearchSkill"],
    }

    def __init__(self) -> None:
        """Initialize the SkillManager."""
        self.settings = get_settings()
        self._engine = None
        self._initialize_db()
        self.graph_integration = SkillGraphIntegration()
        self.skills_dir = Path(__file__).parent.parent / "skills"

    def _initialize_db(self) -> None:
        """Initialize the database connection and create tables if needed."""
        try:
            db_url = (
                f"postgresql://{self.settings.postgres_user}:{self.settings.postgres_password}"
                f"@{self.settings.postgres_host}:{self.settings.postgres_port}/{self.settings.postgres_db}"
            )
            self._engine = create_engine(db_url)

            # Create tables if they don't exist
            Skill.metadata.create_all(self._engine)
            AgentSkill.metadata.create_all(self._engine)
            SkillMetrics.metadata.create_all(self._engine)

            logger.info("SkillManager database initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize SkillManager database: {}", exc)
            raise RuntimeError(f"Database initialization failed: {exc}") from exc

    def _get_session(self) -> Session:
        """Get a database session.

        Returns:
            SQLAlchemy Session instance.
        """
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return Session(self._engine)

    def load_skill(self, skill_name: str) -> Skill | None:
        """Load a skill from the database by name.

        Args:
            skill_name: Name of the skill to load.

        Returns:
            Skill object if found, None otherwise.
        """
        try:
            with self._get_session() as session:
                skill = session.execute(
                    select(Skill).where(Skill.skill_name == skill_name)
                ).scalar_one_or_none()
                return skill
        except Exception as exc:
            logger.error("Failed to load skill {}: {}", skill_name, exc)
            return None

    def load_skill_from_file(self, skill_name: str) -> str | None:
        """Load skill content from markdown file.

        Args:
            skill_name: Name of the skill (without .md extension).

        Returns:
            Skill content as string if found, None otherwise.
        """
        try:
            # Convert skill name to filename (e.g., RiskAssessmentSkill -> risk_assessment_skill.md)
            filename = self._skill_name_to_filename(skill_name)
            file_path = self.skills_dir / filename

            if not file_path.exists():
                logger.warning("Skill file not found: {}", file_path)
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.debug("Loaded skill from file: {}", filename)
            return content

        except Exception as exc:
            logger.error("Failed to load skill from file {}: {}", skill_name, exc)
            return None

    def _skill_name_to_filename(self, skill_name: str) -> str:
        """Convert skill name to filename.

        Args:
            skill_name: Skill name (e.g., RiskAssessmentSkill).

        Returns:
            Filename (e.g., risk_assessment_skill.md).
        """
        # Convert CamelCase to snake_case
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", skill_name)
        snake_case = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
        return f"{snake_case}.md"

    def load_agent_skills(self, agent_id: str) -> list[Skill]:
        """Load all skills assigned to an agent.

        Args:
            agent_id: ID of the agent.

        Returns:
            List of Skill objects assigned to the agent.
        """
        try:
            with self._get_session() as session:
                agent_skills = session.execute(
                    select(AgentSkill).where(AgentSkill.agent_id == agent_id)
                ).scalars().all()

                skills = []
                for agent_skill in agent_skills:
                    skill = session.execute(
                        select(Skill).where(Skill.skill_id == agent_skill.skill_id)
                    ).scalar_one_or_none()
                    if skill:
                        skills.append(skill)

                logger.debug("Loaded {} skills for agent {}", len(skills), agent_id)
                return skills

        except Exception as exc:
            logger.error("Failed to load skills for agent {}: {}", agent_id, exc)
            return []

    def assign_skill(self, agent_id: str, skill_name: str) -> bool:
        """Assign a skill to an agent.

        Args:
            agent_id: ID of the agent.
            skill_name: Name of the skill to assign.

        Returns:
            True if assignment was successful, False otherwise.
        """
        try:
            with self._get_session() as session:
                # Check if skill exists
                skill = session.execute(
                    select(Skill).where(Skill.skill_name == skill_name)
                ).scalar_one_or_none()

                if not skill:
                    logger.warning("Skill not found: {}", skill_name)
                    return False

                # Check if assignment already exists
                existing = session.execute(
                    select(AgentSkill).where(
                        AgentSkill.agent_id == agent_id,
                        AgentSkill.skill_id == skill.skill_id
                    )
                ).scalar_one_or_none()

                if existing:
                    logger.debug("Skill {} already assigned to agent {}", skill_name, agent_id)
                    return True

                # Create assignment
                agent_skill = AgentSkill(
                    agent_id=agent_id,
                    skill_id=skill.skill_id,
                    assigned_at=datetime.utcnow(),
                )
                session.add(agent_skill)
                session.commit()

                # Update graph
                self.graph_integration.create_agent_skill_relationship(agent_id, skill_name)

                logger.info("Assigned skill {} to agent {}", skill_name, agent_id)
                return True

        except Exception as exc:
            logger.error("Failed to assign skill {} to agent {}: {}", skill_name, agent_id, exc)
            return False

    def assign_default_skills(self, agent_id: str, task_type: str) -> bool:
        """Assign default skills to an agent based on task type.

        Args:
            agent_id: ID of the agent.
            task_type: Type of task the agent will handle.

        Returns:
            True if assignment was successful, False otherwise.
        """
        try:
            # Get skills for task type
            skill_names = self.TASK_TYPE_SKILL_MAPPING.get(task_type, [])

            if not skill_names:
                logger.warning("No skill mapping found for task type: {}", task_type)
                return False

            # Assign each skill
            success = True
            for skill_name in skill_names:
                if not self.assign_skill(agent_id, skill_name):
                    logger.warning("Failed to assign skill {} to agent {}", skill_name, agent_id)
                    success = False

            if success:
                logger.info("Assigned {} default skills to agent {} for task type {}", len(skill_names), agent_id, task_type)

            return success

        except Exception as exc:
            logger.error("Failed to assign default skills to agent {}: {}", agent_id, exc)
            return False

    def get_skill_context(self, agent_id: str) -> str:
        """Get skill context for an agent by loading and combining skill methodologies.

        Args:
            agent_id: ID of the agent.

        Returns:
            Combined skill context as a string for prompt injection.
        """
        try:
            skills = self.load_agent_skills(agent_id)

            if not skills:
                logger.debug("No skills found for agent {}", agent_id)
                return ""

            context_parts = ["## Available Skills\n"]

            for skill in skills:
                # Load skill content from file
                skill_content = self.load_skill_from_file(skill.skill_name)

                if skill_content:
                    context_parts.append(f"\n### {skill.skill_name}\n")
                    context_parts.append(skill_content)
                else:
                    # Fallback to database description
                    context_parts.append(f"\n### {skill.skill_name}\n")
                    context_parts.append(f"Description: {skill.description}\n")

            combined_context = "\n".join(context_parts)
            logger.debug("Generated skill context for agent {} with {} skills", agent_id, len(skills))
            return combined_context

        except Exception as exc:
            logger.error("Failed to get skill context for agent {}: {}", agent_id, exc)
            return ""

    def register_skill_from_file(self, filename: str) -> bool:
        """Register a skill from a markdown file in the database.

        Args:
            filename: Name of the skill file (e.g., risk_assessment_skill.md).

        Returns:
            True if registration was successful, False otherwise.
        """
        try:
            file_path = self.skills_dir / filename

            if not file_path.exists():
                logger.warning("Skill file not found: {}", file_path)
                return False

            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract skill name from filename
            skill_name = self._filename_to_skill_name(filename)

            # Extract description from content (first paragraph after description)
            description = self._extract_description(content)

            with self._get_session() as session:
                # Check if skill already exists
                existing = session.execute(
                    select(Skill).where(Skill.skill_name == skill_name)
                ).scalar_one_or_none()

                if existing:
                    logger.debug("Skill already registered: {}", skill_name)
                    return True

                # Create skill
                skill = Skill(
                    skill_name=skill_name,
                    description=description,
                    file_path=str(file_path),
                    created_at=datetime.utcnow(),
                )
                session.add(skill)
                session.commit()

                # Create graph node
                self.graph_integration.create_skill_node(skill_name, description, str(file_path))

                logger.info("Registered skill from file: {}", filename)
                return True

        except Exception as exc:
            logger.error("Failed to register skill from file {}: {}", filename, exc)
            return False

    def _filename_to_skill_name(self, filename: str) -> str:
        """Convert filename to skill name.

        Args:
            filename: Filename (e.g., risk_assessment_skill.md).

        Returns:
            Skill name (e.g., RiskAssessmentSkill).
        """
        # Remove .md extension
        name_without_ext = filename.replace(".md", "")

        # Convert snake_case to CamelCase
        parts = name_without_ext.split("_")
        camel_case = "".join(part.capitalize() for part in parts)

        return camel_case

    def _extract_description(self, content: str) -> str:
        """Extract description from skill markdown content.

        Args:
            content: Skill markdown content.

        Returns:
            Description string.
        """
        lines = content.split("\n")
        in_description = False
        description_lines = []

        for line in lines:
            if line.strip() == "## Description":
                in_description = True
                continue
            if in_description:
                if line.startswith("##"):
                    break
                if line.strip():
                    description_lines.append(line.strip())

        return " ".join(description_lines) if description_lines else "No description available"

    def initialize_skills(self) -> bool:
        """Initialize all skills from the skills directory.

        Returns:
            True if initialization was successful, False otherwise.
        """
        try:
            if not self.skills_dir.exists():
                logger.error("Skills directory not found: {}", self.skills_dir)
                return False

            # Get all .md files
            skill_files = [f for f in os.listdir(self.skills_dir) if f.endswith(".md")]

            if not skill_files:
                logger.warning("No skill files found in {}", self.skills_dir)
                return False

            # Register each skill
            success_count = 0
            for filename in skill_files:
                if self.register_skill_from_file(filename):
                    success_count += 1

            logger.info("Initialized {}/{} skills", success_count, len(skill_files))
            return success_count > 0

        except Exception as exc:
            logger.error("Failed to initialize skills: {}", exc)
            return False

    def record_skill_usage(self, skill_id: int, success: bool = True) -> bool:
        """Record skill usage for metrics tracking.

        Args:
            skill_id: ID of the skill.
            success: Whether the task execution was successful.

        Returns:
            True if recording was successful, False otherwise.
        """
        try:
            with self._get_session() as session:
                # Get or create metrics
                metrics = session.execute(
                    select(SkillMetrics).where(SkillMetrics.skill_id == skill_id)
                ).scalar_one_or_none()

                if not metrics:
                    metrics = SkillMetrics(
                        skill_id=skill_id,
                        usage_count=0,
                        invocation_frequency=0.0,
                        avg_performance_with_skill=0.0,
                        avg_performance_without_skill=0.0,
                        last_updated=datetime.utcnow(),
                    )
                    session.add(metrics)

                # Update metrics
                metrics.usage_count += 1
                metrics.invocation_frequency = metrics.usage_count / max(1, (datetime.utcnow() - metrics.last_updated).days)

                # Update performance with skill
                if success:
                    metrics.avg_performance_with_skill = (
                        0.8 * metrics.avg_performance_with_skill + 0.2 * 1.0
                    )
                else:
                    metrics.avg_performance_with_skill = (
                        0.8 * metrics.avg_performance_with_skill + 0.2 * 0.0
                    )

                metrics.last_updated = datetime.utcnow()
                session.commit()

                logger.debug("Recorded usage for skill {}", skill_id)
                return True

        except Exception as exc:
            logger.error("Failed to record skill usage for skill {}: {}", skill_id, exc)
            return False

    def get_skill_metrics(self, skill_id: int) -> dict[str, Any] | None:
        """Get metrics for a specific skill.

        Args:
            skill_id: ID of the skill.

        Returns:
            Dictionary with skill metrics if found, None otherwise.
        """
        try:
            with self._get_session() as session:
                metrics = session.execute(
                    select(SkillMetrics).where(SkillMetrics.skill_id == skill_id)
                ).scalar_one_or_none()

                if metrics:
                    return {
                        "skill_id": metrics.skill_id,
                        "usage_count": metrics.usage_count,
                        "invocation_frequency": metrics.invocation_frequency,
                        "avg_performance_with_skill": metrics.avg_performance_with_skill,
                        "avg_performance_without_skill": metrics.avg_performance_without_skill,
                        "last_updated": metrics.last_updated.isoformat(),
                    }

                return None

        except Exception as exc:
            logger.error("Failed to get metrics for skill {}: {}", skill_id, exc)
            return None
