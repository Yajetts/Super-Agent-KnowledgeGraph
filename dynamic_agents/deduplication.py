"""Agent deduplication to prevent creation of duplicate dynamic agents."""

from __future__ import annotations

from collections import Counter
from typing import Any

from config.settings import get_settings
from dynamic_agents.agent_registry import DynamicAgentRegistry
from dynamic_agents.models import AgentProfile
from loguru import logger


class AgentDeduplicator:
    """Detect and prevent duplicate agent creation based on capability similarity."""

    def __init__(self, registry: DynamicAgentRegistry | None = None) -> None:
        """Initialize the agent deduplicator.

        Args:
            registry: Agent registry. If None, uses default DynamicAgentRegistry.
        """
        self.registry = registry or DynamicAgentRegistry()
        self.settings = get_settings()

    def calculate_skill_overlap(self, skills1: list[str], skills2: list[str]) -> float:
        """Calculate the overlap between two skill lists using Jaccard similarity.

        Args:
            skills1: First list of skills.
            skills2: Second list of skills.

        Returns:
            Similarity score between 0 and 1.
        """
        if not skills1 or not skills2:
            return 0.0

        set1 = set(skill.lower() for skill in skills1)
        set2 = set(skill.lower() for skill in skills2)

        if not set1 or not set2:
            return 0.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between two descriptions using word overlap.

        Args:
            desc1: First description.
            desc2: Second description.

        Returns:
            Similarity score between 0 and 1.
        """
        if not desc1 or not desc2:
            return 0.0

        # Tokenize and normalize
        words1 = set(word.lower() for word in desc1.split() if len(word) > 3)
        words2 = set(word.lower() for word in desc2.split() if len(word) > 3)

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two agent names.

        Uses normalized name comparison to detect similar names like
        "CarBatteryRiskAnalysisAgent" vs "BatteryRiskAnalysisAgent".

        Args:
            name1: First agent name.
            name2: Second agent name.

        Returns:
            Similarity score between 0 and 1.
        """
        if not name1 or not name2:
            return 0.0

        # Normalize both names by removing common prefixes
        prefixes_to_remove = ["EV", "ElectricVehicle", "Lithium", "Car", "Autonomous", "Quantum", "Satellite"]

        norm1 = name1
        norm2 = name2

        for prefix in prefixes_to_remove:
            if norm1.startswith(prefix):
                norm1 = norm1[len(prefix):]
                break

        for prefix in prefixes_to_remove:
            if norm2.startswith(prefix):
                norm2 = norm2[len(prefix):]
                break

        # If normalized names are identical, return 1.0
        if norm1 == norm2:
            return 1.0

        # Otherwise, use word overlap on the original names
        words1 = set(word.lower() for word in name1.replace("Agent", "").split() if len(word) > 2)
        words2 = set(word.lower() for word in name2.replace("Agent", "").split() if len(word) > 2)

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def calculate_profile_similarity(self, profile1: AgentProfile, profile2: dict[str, Any]) -> float:
        """Calculate overall similarity between an AgentProfile and an agent dictionary.

        Considers:
        - Name similarity (40% weight) - critical for detecting similar agents
        - Skill overlap (40% weight)
        - Description similarity (15% weight)
        - Task type overlap (5% weight)

        Args:
            profile1: First agent profile.
            profile2: Second agent as dictionary.

        Returns:
            Overall similarity score between 0 and 1.
        """
        name_sim = self.calculate_name_similarity(profile1.name, profile2.get("name", ""))
        skill_sim = self.calculate_skill_overlap(profile1.skills, profile2.get("skills", []))
        desc_sim = self.calculate_description_similarity(profile1.description, profile2.get("description", ""))

        # Task type overlap
        task_types1 = set(tt.lower() for tt in profile1.supported_task_types)
        task_types2 = set(tt.lower() for tt in profile2.get("task_types", []))

        if task_types1 and task_types2:
            task_sim = len(task_types1.intersection(task_types2)) / len(task_types1.union(task_types2))
        else:
            task_sim = 0.0

        # Weighted average - name similarity is critical
        overall_sim = 0.4 * name_sim + 0.4 * skill_sim + 0.15 * desc_sim + 0.05 * task_sim

        logger.debug(
            "Similarity between {} and {}: name={:.2f}, skill={:.2f}, desc={:.2f}, task={:.2f}, overall={:.2f}",
            profile1.name,
            profile2.get("name", ""),
            name_sim,
            skill_sim,
            desc_sim,
            task_sim,
            overall_sim,
        )

        return overall_sim

    def find_similar_agents(self, profile: AgentProfile) -> list[tuple[dict[str, Any], float]]:
        """Find existing agents similar to the given profile.

        Args:
            profile: Agent profile to compare against.

        Returns:
            List of (agent_dict, similarity_score) tuples for agents above threshold.
        """
        all_agents = self.registry.get_all_agents()
        threshold = self.settings.agent_deduplication_threshold

        similar_agents = []

        for agent_dict in all_agents:
            # Skip self-comparison
            if agent_dict["name"] == profile.name:
                continue

            similarity = self.calculate_profile_similarity(profile, agent_dict)

            if similarity >= threshold:
                similar_agents.append((agent_dict, similarity))

        # Sort by similarity descending
        similar_agents.sort(key=lambda x: x[1], reverse=True)

        return similar_agents

    def recommend_reuse(self, profile: AgentProfile) -> dict[str, Any] | None:
        """Recommend an existing agent to reuse instead of creating a new one.

        Args:
            profile: Agent profile for the proposed new agent.

        Returns:
            Agent dictionary to reuse if a similar agent exists, None otherwise.
        """
        similar_agents = self.find_similar_agents(profile)

        if similar_agents:
            best_match, similarity = similar_agents[0]
            logger.info(
                "Found similar agent {} with similarity {:.2f} (threshold: {:.2f})",
                best_match["name"],
                similarity,
                self.settings.agent_deduplication_threshold,
            )
            return best_match

        return None

    def normalize_agent_name(self, proposed_name: str, skills: list[str]) -> str:
        """Normalize an agent name to be more general and reusable.

        Converts specific names like "EVBatteryRiskAnalysisAgent" to more general
        names like "BatteryRiskAnalysisAgent".

        Args:
            proposed_name: The proposed agent name.
            skills: The agent's skills.

        Returns:
            Normalized agent name.
        """
        # Remove specific prefixes
        prefixes_to_remove = ["EV", "ElectricVehicle", "Lithium", "Car", "Autonomous", "Quantum", "Satellite"]

        name = proposed_name

        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):]
                logger.info("Removed prefix '{}' from agent name: {} -> {}", prefix, proposed_name, name)
                break

        # Ensure it still starts with a capital letter
        if name:
            name = name[0].upper() + name[1:]

        return name or proposed_name

    def should_create_agent(self, profile: AgentProfile) -> tuple[bool, dict[str, Any] | None]:
        """Determine if a new agent should be created or if an existing one should be reused.

        Args:
            profile: Proposed agent profile.

        Returns:
            Tuple of (should_create, existing_agent_to_reuse).
            If should_create is True, existing_agent_to_reuse is None.
            If should_create is False, existing_agent_to_reuse contains the agent to reuse.
        """
        existing_agent = self.recommend_reuse(profile)

        if existing_agent:
            logger.info(
                "Reusing existing agent {} instead of creating new agent {}",
                existing_agent["name"],
                profile.name,
            )
            return False, existing_agent

        logger.info("No similar agent found, proceeding with creation of {}", profile.name)
        return True, None
