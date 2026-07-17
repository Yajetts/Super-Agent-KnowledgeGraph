"""Factory for turning selected agent names into concrete agent objects."""

from __future__ import annotations

from loguru import logger

from agents.base_agent import BaseAgent
from agents.research_agent import ResearchAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from agents.dynamic_agent import DynamicAgent
from dynamic_agents.agent_registry import DynamicAgentRegistry
from services.llm_service import LLMService, get_llm_service


class AgentFactory:
    """Create supported agent instances from selected agent names."""

    _agent_map = {
        "ResearchAgent": ResearchAgent,
        "RiskAgent": RiskAgent,
        "StrategyAgent": StrategyAgent,
    }

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or get_llm_service()
        self.dynamic_agent_registry = DynamicAgentRegistry()

    def create_agent(self, agent_name: str) -> BaseAgent:
        """Create a single agent instance by name."""
        # Check if it's a dynamic agent
        if self.dynamic_agent_registry.agent_exists(agent_name):
            agent_data = self.dynamic_agent_registry.get_agent_by_name(agent_name)
            if agent_data and agent_data.get("is_dynamic"):
                logger.info("Creating dynamic agent: {}", agent_name)
                return DynamicAgent(agent_name=agent_name, llm_service=self.llm_service)

        # If not in registry, check repository directly for newly created agents
        from dynamic_agents.repository import DynamicAgentRepository
        repository = DynamicAgentRepository()
        try:
            if repository.get_agent(agent_name):
                logger.info("Found dynamic agent in repository, creating: {}", agent_name)
                return DynamicAgent(agent_name=agent_name, llm_service=self.llm_service)
        except Exception as exc:
            logger.debug("Agent not found in repository: {}", exc)

        # Fall back to static agents
        agent_class = self._agent_map.get(agent_name)
        if agent_class is None:
            raise ValueError(f"Unsupported agent requested: {agent_name}")
        return agent_class(llm_service=self.llm_service)

    def create_agents(self, agent_names: list[str]) -> list[BaseAgent]:
        """Create agent instances in the supplied order."""
        return [self.create_agent(agent_name) for agent_name in agent_names]