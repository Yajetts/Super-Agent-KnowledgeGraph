"""Relevance-based agent selection to prevent unrelated agents from participating."""

from __future__ import annotations

from collections import Counter
from typing import Any

from config.settings import get_settings
from dynamic_agents.agent_registry import DynamicAgentRegistry
from loguru import logger


class RelevanceMatcher:
    """Match agents to tasks based on skill and task relevance."""

    def __init__(self, registry: DynamicAgentRegistry | None = None) -> None:
        """Initialize the relevance matcher.

        Args:
            registry: Agent registry. If None, uses default DynamicAgentRegistry.
        """
        self.registry = registry or DynamicAgentRegistry()
        self.settings = get_settings()

    def calculate_skill_similarity(self, required_skills: list[str], agent_skills: list[str]) -> float:
        """Calculate similarity between required skills and agent skills.

        Uses Jaccard similarity: intersection / union.

        Args:
            required_skills: Skills required for the task.
            agent_skills: Skills possessed by the agent.

        Returns:
            Similarity score between 0 and 1.
        """
        if not required_skills or not agent_skills:
            return 0.0

        required_set = set(skill.lower() for skill in required_skills)
        agent_set = set(skill.lower() for skill in agent_skills)

        if not required_set or not agent_set:
            return 0.0

        intersection = required_set.intersection(agent_set)
        union = required_set.union(agent_set)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def calculate_task_similarity(self, task_type: str, agent_task_types: list[str]) -> float:
        """Calculate similarity between task type and agent's supported task types.

        Args:
            task_type: The task type being executed.
            agent_task_types: Task types supported by the agent.

        Returns:
            Similarity score between 0 and 1.
        """
        if not task_type or not agent_task_types:
            return 0.0

        task_type_lower = task_type.lower()
        agent_task_types_lower = [t.lower() for t in agent_task_types]

        # Exact match
        if task_type_lower in agent_task_types_lower:
            return 1.0

        # Partial match (substring)
        for agent_task in agent_task_types_lower:
            if task_type_lower in agent_task or agent_task in task_type_lower:
                return 0.8

        return 0.0

    def calculate_name_similarity(self, task_query: str, agent_name: str) -> float:
        """Calculate similarity between task query and agent name.

        The agent name is often the most direct indicator of what the agent does.
        Uses word overlap and keyword matching.

        Args:
            task_query: The task query.
            agent_name: The agent's name.

        Returns:
            Similarity score between 0 and 1.
        """
        if not task_query or not agent_name:
            return 0.0

        # Normalize agent name by removing "Agent" suffix and splitting camelCase
        normalized_name = agent_name.replace("Agent", "")
        # Split camelCase into words (e.g., "MarsResourceFeasibility" -> ["Mars", "Resource", "Feasibility"])
        import re
        # Split on uppercase letters followed by lowercase
        name_words = re.findall(r'[A-Z][a-z]+|[a-z]+', normalized_name)
        name_words = set(word.lower() for word in name_words if len(word) > 2)

        # Tokenize task query
        task_words = set(word.lower() for word in task_query.split() if len(word) > 2)

        if not task_words or not name_words:
            return 0.0

        intersection = task_words.intersection(name_words)
        union = task_words.union(name_words)

        if not union:
            return 0.0

        # Base similarity from word overlap
        similarity = len(intersection) / len(union)

        # Boost similarity if key words match
        key_words = ["mars", "feasibility", "resource", "market", "risk", "battery", "car", "ev", "space", "extraction", "quantum", "encryption", "computing", "security", "privacy", "blockchain", "ai", "artificial", "intelligence", "machine", "learning", "data", "analysis"]
        for key_word in key_words:
            if key_word in task_words and key_word in name_words:
                similarity = min(1.0, similarity + 0.3)

        # Boost for partial matches (substring)
        for task_word in task_words:
            for name_word in name_words:
                if task_word in name_word or name_word in task_word:
                    similarity = min(1.0, similarity + 0.1)

        logger.info(
            "Name similarity between '{}' and '{}': task_words={}, name_words={}, intersection={}, similarity={:.2f}",
            task_query,
            agent_name,
            task_words,
            name_words,
            intersection,
            similarity,
        )

        return similarity

    def calculate_description_similarity(self, task_query: str, agent_description: str) -> float:
        """Calculate similarity between task query and agent description.

        Uses word overlap as a simple similarity metric.

        Args:
            task_query: The task query.
            agent_description: The agent's description.

        Returns:
            Similarity score between 0 and 1.
        """
        if not task_query or not agent_description:
            return 0.0

        # Tokenize and normalize
        task_words = set(word.lower() for word in task_query.split() if len(word) > 3)
        desc_words = set(word.lower() for word in agent_description.split() if len(word) > 3)

        if not task_words or not desc_words:
            return 0.0

        intersection = task_words.intersection(desc_words)
        union = task_words.union(desc_words)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def calculate_overall_relevance(
        self,
        required_skills: list[str],
        task_type: str,
        task_query: str,
        agent: dict[str, Any],
    ) -> float:
        """Calculate overall relevance score for an agent.

        Combines name similarity, skill similarity, task similarity, and description similarity
        with weighted averages.

        Args:
            required_skills: Skills required for the task.
            task_type: Type of task being executed.
            task_query: The task query.
            agent: Agent dictionary with skills, description, and task_types.

        Returns:
            Overall relevance score between 0 and 1.
        """
        name_sim = self.calculate_name_similarity(task_query, agent.get("name", ""))
        skill_sim = self.calculate_skill_similarity(required_skills, agent.get("skills", []))
        task_sim = self.calculate_task_similarity(task_type, agent.get("task_types", []))
        desc_sim = self.calculate_description_similarity(task_query, agent.get("description", ""))

        # Weighted average: name (60%), skills (25%), task type (10%), description (5%)
        # Name similarity is critical for detecting domain relevance
        overall_score = 0.6 * name_sim + 0.25 * skill_sim + 0.1 * task_sim + 0.05 * desc_sim

        logger.info(
            "Relevance for {}: name={:.2f}, skill={:.2f}, task={:.2f}, desc={:.2f}, overall={:.2f}",
            agent.get("name", ""),
            name_sim,
            skill_sim,
            task_sim,
            desc_sim,
            overall_score,
        )

        return overall_score

    def rank_agents(
        self,
        required_skills: list[str],
        task_type: str,
        task_query: str,
        agents: list[dict[str, Any]],
    ) -> list[tuple[dict[str, Any], float]]:
        """Rank agents by relevance to the task.

        Args:
            required_skills: Skills required for the task.
            task_type: Type of task being executed.
            task_query: The task query.
            agents: List of agent dictionaries.

        Returns:
            List of (agent, relevance_score) tuples sorted by relevance descending.
        """
        scored_agents = []

        for agent in agents:
            relevance = self.calculate_overall_relevance(required_skills, task_type, task_query, agent)
            scored_agents.append((agent, relevance))

        # Sort by relevance descending
        scored_agents.sort(key=lambda x: x[1], reverse=True)

        return scored_agents

    def filter_irrelevant_agents(
        self,
        required_skills: list[str],
        task_type: str,
        task_query: str,
        agents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter out agents below the relevance threshold.

        Args:
            required_skills: Skills required for the task.
            task_type: Type of task being executed.
            task_query: The task query.
            agents: List of agent dictionaries.

        Returns:
            List of agents that meet the relevance threshold.
        """
        threshold = self.settings.min_agent_similarity
        logger.info("Filtering agents with relevance threshold: {}", threshold)

        scored_agents = self.rank_agents(required_skills, task_type, task_query, agents)

        relevant_agents = []
        for agent, score in scored_agents:
            if score >= threshold:
                logger.info("Agent {} passed relevance check with score: {:.2f}", agent["name"], score)
                relevant_agents.append(agent)
            else:
                logger.info(
                    "Agent {} failed relevance check with score: {:.2f} (threshold: {:.2f})",
                    agent["name"],
                    score,
                    threshold,
                )

        return relevant_agents

    def select_top_k_agents(
        self,
        required_skills: list[str],
        task_type: str,
        task_query: str,
        max_agents: int | None = None,
    ) -> list[dict[str, Any]]:
        """Select the top K most relevant agents for a task.

        For complex queries, this method selects multiple agents with moderate relevance
        to cover different aspects of the task, rather than filtering strictly by threshold.

        Args:
            required_skills: Skills required for the task.
            task_type: Type of task being executed.
            task_query: The task query.
            max_agents: Maximum number of agents to select. If None, uses settings.

        Returns:
            List of selected agent dictionaries.
        """
        if max_agents is None:
            max_agents = self.settings.max_dynamic_agents_per_task

        # Get all agents
        all_agents = self.registry.get_all_agents()

        # Rank all agents by relevance
        scored_agents = self.rank_agents(required_skills, task_type, task_query, all_agents)

        # Select top K agents regardless of threshold for multi-agent collaboration
        # This allows selecting multiple agents with moderate relevance for complex queries
        top_agents = [agent for agent, score in scored_agents[:max_agents]]

        logger.info("Selected {} agents for task: {}", len(top_agents), task_query)

        return top_agents

    def select_agents_by_aspects(
        self,
        required_skills: list[str],
        task_type: str,
        task_query: str,
        max_agents: int | None = None,
    ) -> list[dict[str, Any]]:
        """Select agents by matching them to different aspects of the query.

        This method breaks down the query into different aspects and selects agents
        that are most relevant to each aspect, enabling multi-agent collaboration.

        Args:
            required_skills: Skills required for the task.
            task_type: Type of task being executed.
            task_query: The task query.
            max_agents: Maximum number of agents to select. If None, uses settings.

        Returns:
            List of selected agent dictionaries.
        """
        if max_agents is None:
            max_agents = self.settings.max_dynamic_agents_per_task

        # Get all agents
        all_agents = self.registry.get_all_agents()

        # Rank all agents by relevance
        scored_agents = self.rank_agents(required_skills, task_type, task_query, all_agents)

        # Select top K agents regardless of threshold
        top_agents = [agent for agent, score in scored_agents[:max_agents]]

        # Ensure diversity by selecting agents with different primary skills
        diverse_agents = []
        seen_skills = set()

        for agent in top_agents:
            agent_skills = set(agent.get("skills", []))
            # Check if this agent brings new skills to the team
            new_skills = agent_skills - seen_skills
            if new_skills or not diverse_agents:  # Always include the first agent
                diverse_agents.append(agent)
                seen_skills.update(agent_skills)

            if len(diverse_agents) >= max_agents:
                break

        logger.info("Selected {} diverse agents for task: {}", len(diverse_agents), task_query)

        return diverse_agents
