"""Tests for the multi-agent workflow orchestration layer."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api import routes
from app.main import app
from superagent.agent_factory import AgentFactory
from superagent.agent_selector import AgentSelector
from superagent.controller import SuperAgentController
from superagent.context_models import Finding, Recommendation, Risk
from superagent.task_analyzer import TaskAnalyzer


class DummyLLMService:
    """Simple stub that returns prompt-specific bullet points."""

    def generate(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "research analyst" in prompt_lower:
            return "- Research fact\n- Research insight"
        if "risk assessment specialist" in prompt_lower:
            return "- Risk one\n- Risk two"
        return "- Recommendation one\n- Recommendation two"


def test_task_classification_examples() -> None:
    """Verify the analyzer classifies the documented example queries."""
    analyzer = TaskAnalyzer()

    assert analyzer.classify_task("Analyze Tesla expansion into India") == "business_analysis"
    assert analyzer.classify_task("Research quantum computing startups") == "technology_research"
    assert analyzer.classify_task("Assess cybersecurity risks in healthcare AI") == "risk_assessment"


def test_skill_extraction_matches_task_type() -> None:
    """Verify required skills are mapped deterministically from task type."""
    analyzer = TaskAnalyzer()

    assert analyzer.extract_required_skills("Analyze Tesla expansion into India") == [
        "research",
        "risk_analysis",
        "strategy",
    ]
    assert analyzer.extract_required_skills("Research quantum computing startups") == ["research"]


def test_agent_selector_prefers_supported_workflow_agents() -> None:
    """Verify the selector returns the supported sequential workflow."""
    selector = AgentSelector()

    assert selector.select_agents(["research", "risk_analysis", "strategy"]) == [
        "ResearchAgent",
        "RiskAgent",
        "StrategyAgent",
    ]


def test_agent_factory_creates_supported_agents() -> None:
    """Verify the factory converts selected names into concrete agent objects."""
    factory = AgentFactory(llm_service=DummyLLMService())

    agents = factory.create_agents(["ResearchAgent", "RiskAgent", "StrategyAgent"])

    assert [agent.name for agent in agents] == ["ResearchAgent", "RiskAgent", "StrategyAgent"]


def test_controller_executes_workflow_sequentially() -> None:
    """Verify the controller returns the final workflow result after running all agents."""
    controller = SuperAgentController(llm_service=DummyLLMService())

    result = controller.execute_workflow("Analyze Tesla expansion into India")

    assert result.model_dump() == {
        "query": "Analyze Tesla expansion into India",
        "task_type": "business_analysis",
        "agents_used": ["ResearchAgent", "RiskAgent", "StrategyAgent"],
        "findings": [
            {
                "source_agent": "ResearchAgent",
                "category": "general",
                "content": "Research fact",
                "confidence": 0.5,
            },
            {
                "source_agent": "ResearchAgent",
                "category": "general",
                "content": "Research insight",
                "confidence": 0.5,
            },
        ],
        "risks": [
            {
                "source_agent": "RiskAgent",
                "description": "Risk one",
                "severity": "medium",
            },
            {
                "source_agent": "RiskAgent",
                "description": "Risk two",
                "severity": "medium",
            },
        ],
        "recommendations": [
            {
                "source_agent": "StrategyAgent",
                "content": "Recommendation one",
                "priority": "medium",
            },
            {
                "source_agent": "StrategyAgent",
                "content": "Recommendation two",
                "priority": "medium",
            },
        ],
    }


def test_execute_endpoint_returns_workflow_result() -> None:
    """Verify the FastAPI endpoint exposes the sequential workflow result."""
    routes.controller = SuperAgentController(llm_service=DummyLLMService())
    client = TestClient(app)

    response = client.post("/execute", json={"query": "Analyze Tesla expansion into India"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "Analyze Tesla expansion into India",
        "task_type": "business_analysis",
        "agents_used": ["ResearchAgent", "RiskAgent", "StrategyAgent"],
        "findings": [
            {
                "source_agent": "ResearchAgent",
                "category": "general",
                "content": "Research fact",
                "confidence": 0.5,
            },
            {
                "source_agent": "ResearchAgent",
                "category": "general",
                "content": "Research insight",
                "confidence": 0.5,
            },
        ],
        "risks": [
            {
                "source_agent": "RiskAgent",
                "description": "Risk one",
                "severity": "medium",
            },
            {
                "source_agent": "RiskAgent",
                "description": "Risk two",
                "severity": "medium",
            },
        ],
        "recommendations": [
            {
                "source_agent": "StrategyAgent",
                "content": "Recommendation one",
                "priority": "medium",
            },
            {
                "source_agent": "StrategyAgent",
                "content": "Recommendation two",
                "priority": "medium",
            },
        ],
    }


def test_controller_rejects_empty_query() -> None:
    """Verify invalid input is rejected before any agent execution."""
    controller = SuperAgentController(llm_service=DummyLLMService())

    try:
        controller.execute_workflow("   ")
    except ValueError as exc:
        assert "Query must not be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty query")