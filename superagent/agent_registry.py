"""Static agent registry for deterministic agent selection."""

from __future__ import annotations


class AgentRegistry:
    """Static registry of the currently supported agents."""

    _agents: list[dict[str, list[str] | str]] = [
        {"name": "ResearchAgent", "skills": ["research"]},
        {"name": "MarketAnalysisAgent", "skills": ["research", "market_analysis"]},
        {"name": "RiskAgent", "skills": ["risk_analysis"]},
        {"name": "StrategyAgent", "skills": ["strategy"]},
    ]

    @classmethod
    def get_all_agents(cls) -> list[dict[str, list[str] | str]]:
        """Return all registered agents."""
        return [dict(agent) for agent in cls._agents]

    @classmethod
    def get_agent_by_name(cls, name: str) -> dict[str, list[str] | str] | None:
        """Return a registered agent by name, if it exists."""
        for agent in cls._agents:
            if agent["name"] == name:
                return dict(agent)
        return None

    @classmethod
    def find_agents_by_skill(cls, skill: str) -> list[dict[str, list[str] | str]]:
        """Return agents that advertise a given skill."""
        return [dict(agent) for agent in cls._agents if skill in agent["skills"]]