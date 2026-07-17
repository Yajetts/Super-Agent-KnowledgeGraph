"""Tests for the sequential agent implementations."""

from __future__ import annotations

from agents import ResearchAgent, RiskAgent, StrategyAgent
from superagent.context_models import Finding, GraphContext, Recommendation, Risk
from superagent.task_context import TaskContext


class DummyLLMService:
    """Simple stub that returns deterministic bullet points."""

    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, prompt: str) -> str:
        return self.response


class RecordingLLMService(DummyLLMService):
    """LLM stub that records prompts for assertions."""

    def __init__(self, response: str) -> None:
        super().__init__(response)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def test_research_agent_updates_context() -> None:
    """Ensure the research agent stores bullet points in the shared context."""
    agent = ResearchAgent(llm_service=DummyLLMService("- Fact one\n- Fact two"))
    context = TaskContext(query="Analyze Tesla expansion into India", task_type="business_analysis")

    updated_context = agent.execute(context)

    assert updated_context.agent_history == ["ResearchAgent"]
    assert updated_context.findings == [
        Finding(source_agent="ResearchAgent", category="general", content="Fact one", confidence=0.5),
        Finding(source_agent="ResearchAgent", category="general", content="Fact two", confidence=0.5),
    ]


def test_risk_agent_updates_context() -> None:
    """Ensure the risk agent stores bullet points in the shared context."""
    agent = RiskAgent(llm_service=DummyLLMService("- Risk one\n- Risk two"))
    context = TaskContext(
        query="Analyze Tesla expansion into India",
        task_type="business_analysis",
        findings=[Finding(source_agent="ResearchAgent", category="market", content="Fact one", confidence=0.5)],
    )

    updated_context = agent.execute(context)

    assert updated_context.agent_history == ["RiskAgent"]
    assert updated_context.risks == [
        Risk(source_agent="RiskAgent", description="Risk one", severity="medium"),
        Risk(source_agent="RiskAgent", description="Risk two", severity="medium"),
    ]


def test_strategy_agent_updates_context() -> None:
    """Ensure the strategy agent stores bullet points in the shared context."""
    agent = StrategyAgent(llm_service=DummyLLMService("- Recommendation one\n- Recommendation two"))
    context = TaskContext(
        query="Analyze Tesla expansion into India",
        task_type="business_analysis",
        findings=[Finding(source_agent="ResearchAgent", category="market", content="Fact one", confidence=0.5)],
        risks=[Risk(source_agent="RiskAgent", description="Risk one", severity="high")],
    )

    updated_context = agent.execute(context)

    assert updated_context.agent_history == ["StrategyAgent"]
    assert updated_context.recommendations == [
        Recommendation(source_agent="StrategyAgent", content="Recommendation one", priority="medium"),
        Recommendation(source_agent="StrategyAgent", content="Recommendation two", priority="medium"),
    ]


def test_agents_receive_graph_context_in_prompt() -> None:
    """Ensure agent prompts include the graph context summary when available."""
    llm = RecordingLLMService('- {"category": "market", "content": "Demand rising", "confidence": 0.7}')
    context = TaskContext(
        query="Analyze Tesla expansion into India",
        task_type="business_analysis",
        graph_context=GraphContext(
            related_tasks=[{"task_id": "task-1", "query": "Prior expansion analysis"}],
            summary="Historical analyses suggest local partnerships reduce entry friction.",
        ),
    )

    research_agent = ResearchAgent(llm_service=llm)
    research_agent.execute(context)

    assert llm.prompts
    assert "Graph context summary" in llm.prompts[0]
    assert "local partnerships" in llm.prompts[0]
