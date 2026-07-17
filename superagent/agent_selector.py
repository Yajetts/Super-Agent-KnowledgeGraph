"""Rule-based agent selection for the SuperAgent workflow."""

from __future__ import annotations

from dynamic_agents.agent_registry import DynamicAgentRegistry


class AgentSelector:
    """Choose the best agent combination for a structured task."""

    _preferred_agents_by_skill: dict[str, str] = {
        "research": "ResearchAgent",
        "risk_analysis": "RiskAgent",
        "strategy": "StrategyAgent",
    }

    _supported_agents = {"ResearchAgent", "RiskAgent", "StrategyAgent"}

    def __init__(self, registry: DynamicAgentRegistry | None = None) -> None:
        """Initialize the agent selector.

        Args:
            registry: Agent registry. If None, uses default DynamicAgentRegistry.
        """
        self.registry = registry or DynamicAgentRegistry()

    def select_agents(self, required_skills: list[str]) -> list[str]:
        """Return the best matching agent names for the requested skills."""
        selected_agents: list[str] = []
        seen_agents: set[str] = set()

        for skill in required_skills:
            preferred_agent = self._preferred_agents_by_skill.get(skill)
            if preferred_agent is None:
                # Use dynamic agent registry to find agents with this skill
                matching_agents = self.registry.find_agents_by_skill(skill)
                preferred_agent = next(
                    (
                        agent["name"]
                        for agent in matching_agents
                        if agent["name"] in self._supported_agents or agent.get("is_dynamic")
                    ),
                    None,
                )

            if preferred_agent is not None and preferred_agent not in seen_agents:
                selected_agents.append(preferred_agent)
                seen_agents.add(preferred_agent)

        if not selected_agents:
            selected_agents.append("ResearchAgent")

        return selected_agents

    def select(self, task_analysis: dict[str, object]) -> list[str]:
        """Compatibility wrapper for callers that still pass analysis dictionaries."""
        if isinstance(task_analysis, dict):
            required_skills = list(task_analysis.get("required_skills", []))
        else:
            required_skills = []
        return self.select_agents(required_skills)
