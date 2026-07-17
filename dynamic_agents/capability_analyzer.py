"""Capability analyzer for detecting missing agent skills."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from dynamic_agents.agent_registry import DynamicAgentRegistry
from dynamic_agents.models import CapabilityGap, TaskAnalysis
from services.llm_service import LLMService, get_llm_service


class CapabilityAnalyzer:
    """Analyzes task requirements and detects capability gaps in existing agents."""

    def __init__(
        self,
        llm_service: LLMService | None = None,
        registry: DynamicAgentRegistry | None = None,
    ) -> None:
        """Initialize the capability analyzer.

        Args:
            llm_service: LLM service for skill extraction. If None, uses default.
            registry: Agent registry. If None, uses default.
        """
        self.llm_service = llm_service or get_llm_service()
        self.registry = registry or DynamicAgentRegistry()

    def analyze_task(self, task_query: str) -> TaskAnalysis:
        """Analyze a task to identify required skills and capability gaps.

        Args:
            task_query: The task description/query to analyze.

        Returns:
            TaskAnalysis containing required skills, gaps, and coverage score.
        """
        logger.info("Analyzing task: {}", task_query)

        # Step 1: Identify required skills
        required_skills = self.identify_required_skills(task_query)
        logger.info("Identified required skills: {}", required_skills)

        # Step 2: Infer task type
        task_type = self._infer_task_type(task_query, required_skills)
        logger.info("Inferred task type: {}", task_type)

        # Step 3: Find capability gaps
        capability_gaps = self.find_capability_gaps(required_skills)
        logger.info("Found {} capability gaps", len(capability_gaps))

        # Step 4: Calculate coverage score
        coverage_score = self._calculate_coverage_score(required_skills, capability_gaps)
        logger.info("Coverage score: {:.2f}", coverage_score)

        # Step 5: Determine if agent creation is needed
        should_create_agent = self.recommend_agent_creation(coverage_score, capability_gaps)
        logger.info("Should create agent: {}", should_create_agent)

        return TaskAnalysis(
            task_query=task_query,
            task_type=task_type,
            required_skills=required_skills,
            capability_gaps=capability_gaps,
            coverage_score=coverage_score,
            should_create_agent=should_create_agent,
        )

    def identify_required_skills(self, task_query: str) -> list[str]:
        """Identify the skills required to complete a task.

        Args:
            task_query: The task description.

        Returns:
            List of required skill names.
        """
        prompt = f"""Analyze the following task and identify the specific skills required to complete it.

Task: {task_query}

Return a JSON array of skill names (strings). Skills should be specific and actionable.
Example: ["research", "data_analysis", "technical_writing"]

Respond with ONLY the JSON array, no other text."""

        try:
            response = self.llm_service.generate(prompt)
            skills = json.loads(response)
            if isinstance(skills, list):
                return [str(skill).strip().lower() for skill in skills if skill]
            return []
        except Exception as exc:
            logger.error("Failed to identify required skills: {}", exc)
            return []

    def find_capability_gaps(self, required_skills: list[str]) -> list[CapabilityGap]:
        """Find gaps between required skills and available agent capabilities.

        Args:
            required_skills: List of skills required for the task.

        Returns:
            List of CapabilityGap objects representing missing skills.
        """
        gaps: list[CapabilityGap] = []

        for skill in required_skills:
            # Check if any agent has this skill
            agents_with_skill = self.registry.find_agents_by_skill(skill)

            if not agents_with_skill:
                # No agent has this skill - it's a gap
                gaps.append(
                    CapabilityGap(
                        required_skill=skill,
                        confidence=1.0,
                        context=f"No existing agent possesses the '{skill}' skill.",
                    )
                )
            else:
                # Check if the skill is adequately covered
                # For now, we consider it covered if at least one agent has it
                # This could be enhanced with more sophisticated coverage analysis
                pass

        return gaps

    def recommend_agent_creation(
        self, coverage_score: float, capability_gaps: list[CapabilityGap]
    ) -> bool:
        """Recommend whether a new agent should be created.

        Args:
            coverage_score: How well existing agents cover required skills (0.0-1.0).
            capability_gaps: List of detected capability gaps.

        Returns:
            True if a new agent should be created, False otherwise.
        """
        # Create agent if coverage is below threshold
        COVERAGE_THRESHOLD = 0.5

        if coverage_score < COVERAGE_THRESHOLD:
            logger.debug(
                "Coverage score {:.2f} below threshold {:.2f}, recommending agent creation",
                coverage_score,
                COVERAGE_THRESHOLD,
            )
            return True

        # Also create if there are critical gaps
        if len(capability_gaps) > 0:
            logger.debug(
                "Found {} capability gaps, recommending agent creation",
                len(capability_gaps),
            )
            return True

        return False

    def _infer_task_type(self, task_query: str, required_skills: list[str]) -> str:
        """Infer the task type from the query and required skills.

        Args:
            task_query: The task description.
            required_skills: List of identified required skills.

        Returns:
            Inferred task type as a string.
        """
        # Simple heuristic-based inference
        # This could be enhanced with LLM-based classification

        query_lower = task_query.lower()
        skills_str = " ".join(required_skills)

        if any(
            keyword in query_lower
            for keyword in ["analyze", "analysis", "assess", "evaluate"]
        ):
            if "risk" in query_lower or "security" in query_lower:
                return "risk_analysis"
            if "market" in query_lower or "competitive" in query_lower:
                return "market_analysis"
            return "analysis"

        if any(keyword in query_lower for keyword in ["research", "investigate", "study"]):
            return "research"

        if any(keyword in query_lower for keyword in ["strategy", "plan", "recommend"]):
            return "strategy"

        if "cybersecurity" in query_lower or "security" in query_lower:
            return "cybersecurity"

        # Default to a generic type based on primary skill
        if required_skills:
            return required_skills[0]

        return "general"

    def _calculate_coverage_score(
        self, required_skills: list[str], capability_gaps: list[CapabilityGap]
    ) -> float:
        """Calculate how well existing agents cover required skills.

        Args:
            required_skills: List of required skills.
            capability_gaps: List of detected capability gaps.

        Returns:
            Coverage score between 0.0 and 1.0.
        """
        if not required_skills:
            return 1.0

        covered_skills = len(required_skills) - len(capability_gaps)
        coverage_score = covered_skills / len(required_skills)

        return coverage_score
