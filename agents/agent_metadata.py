"""Static metadata for supported agents."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AgentMetadata(BaseModel):
	"""Describe an agent for graph persistence and discovery."""

	name: str
	description: str
	skills: list[str] = Field(default_factory=list)

	model_config = ConfigDict(extra="forbid")


AGENT_METADATA: dict[str, AgentMetadata] = {
	"ResearchAgent": AgentMetadata(
		name="ResearchAgent",
		description="Generates concise research findings.",
		skills=["research"],
	),
	"MarketAnalysisAgent": AgentMetadata(
		name="MarketAnalysisAgent",
		description="Analyzes market structure, demand, and competitive positioning.",
		skills=["research", "market_analysis"],
	),
	"RiskAgent": AgentMetadata(
		name="RiskAgent",
		description="Generates concise risk analysis findings.",
		skills=["research", "risk_analysis"],
	),
	"StrategyAgent": AgentMetadata(
		name="StrategyAgent",
		description="Generates concise strategy recommendations.",
		skills=["strategy"],
	),
}


def get_agent_metadata(name: str) -> AgentMetadata | None:
	"""Return metadata for a named agent, if it exists."""
	return AGENT_METADATA.get(name)


def get_all_agent_metadata() -> list[AgentMetadata]:
	"""Return all registered agent metadata entries."""
	return [metadata.model_copy() for metadata in AGENT_METADATA.values()]