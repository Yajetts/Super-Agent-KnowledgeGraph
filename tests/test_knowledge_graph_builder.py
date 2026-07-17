"""Tests for the knowledge graph builder."""

from __future__ import annotations

from graph.knowledge_graph_builder import KnowledgeGraphBuilder
from superagent.context_models import Finding, Recommendation, Risk, TaskContext


class RecordingRepository:
	def __init__(self, owner: "RecordingGraphManager") -> None:
		self.owner = owner

	def create_skill_node(self, name: str):
		self.owner.calls.append(("create_skill_node", (name,)))
		return [{"name": name}]


class RecordingGraphManager:
	def __init__(self) -> None:
		self.calls: list[tuple[str, tuple[object, ...]]] = []
		self.repository = RecordingRepository(self)

	def create_task_node(self, *args):
		self.calls.append(("create_task_node", args))
		return [{"task": args[0]}]

	def create_agent_node(self, *args):
		self.calls.append(("create_agent_node", args))
		return [{"agent": args[0]}]

	def create_skill_node(self, *args):
		self.calls.append(("create_skill_node", args))
		return [{"skill": args[0]}]

	def create_finding_node(self, *args):
		self.calls.append(("create_finding_node", args))
		return [{"finding": args[0]}]

	def create_risk_node(self, *args):
		self.calls.append(("create_risk_node", args))
		return [{"risk": args[0]}]

	def create_recommendation_node(self, *args):
		self.calls.append(("create_recommendation_node", args))
		return [{"recommendation": args[0]}]

	def create_relationship(self, *args, **kwargs):
		self.calls.append(("create_relationship", args))
		return [{"relationship": args[2]}]


def test_builder_creates_task_agents_findings_and_relationships() -> None:
	"""Ensure a completed workflow is converted into graph nodes and edges."""
	manager = RecordingGraphManager()
	builder = KnowledgeGraphBuilder(manager)  # type: ignore[arg-type]
	context = TaskContext(
		query="Analyze Tesla expansion into India",
		task_type="business_analysis",
		findings=[Finding(source_agent="ResearchAgent", category="market", content="EV demand is growing", confidence=0.9)],
		risks=[Risk(source_agent="RiskAgent", description="Policy change", severity="high")],
		recommendations=[Recommendation(source_agent="StrategyAgent", content="Partner locally", priority="high")],
		agent_history=["ResearchAgent", "RiskAgent", "StrategyAgent"],
		metadata={"selected_agents": ["ResearchAgent", "RiskAgent", "StrategyAgent"]},
	)

	summary = builder.build_from_context(context)

	assert summary["findings"] == 1
	assert context.metadata["task_id"]
	assert any(call[0] == "create_task_node" for call in manager.calls)
	assert any(call[0] == "create_skill_node" for call in manager.calls)
	assert any(call[0] == "create_relationship" and call[1][2] == "TASK_USED_AGENT" for call in manager.calls)
	assert any(call[0] == "create_relationship" and call[1][2] == "TASK_GENERATED_FINDING" for call in manager.calls)
	assert any(call[0] == "create_relationship" and call[1][2] == "TASK_GENERATED_RISK" for call in manager.calls)
	assert any(call[0] == "create_relationship" and call[1][2] == "TASK_GENERATED_RECOMMENDATION" for call in manager.calls)