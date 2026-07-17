"""Phase 3 tests for structured shared context behavior."""

from __future__ import annotations

from core.output_parser import parse_findings, parse_recommendations, parse_risks
from superagent.context_manager import ContextManager
from superagent.context_models import Finding, Recommendation, Risk, TaskContext, WorkflowResult


def test_context_models_validate_structured_data() -> None:
    """Ensure the structured context models accept and preserve typed data."""
    finding = Finding(source_agent="ResearchAgent", category="market", content="India EV growth", confidence=0.87)
    risk = Risk(source_agent="RiskAgent", description="Supply chain pressure", severity="high")
    recommendation = Recommendation(source_agent="StrategyAgent", content="Expand through local partners", priority="high")

    context = TaskContext(
        query="Analyze EV expansion",
        task_type="business_analysis",
        findings=[finding],
        risks=[risk],
        recommendations=[recommendation],
    )

    assert context.findings[0].model_dump() == finding.model_dump()
    assert context.risks[0].model_dump() == risk.model_dump()
    assert context.recommendations[0].model_dump() == recommendation.model_dump()


def test_context_manager_updates_shared_context() -> None:
    """Ensure the context manager creates and updates shared state safely."""
    manager = ContextManager()
    context = manager.create_context(query="Analyze EV expansion", task_type="business_analysis")

    manager.add_finding(
        context,
        Finding(source_agent="ResearchAgent", category="market", content="India EV growth", confidence=0.87),
    )
    manager.add_risk(context, Risk(source_agent="RiskAgent", description="Supply chain pressure", severity="high"))
    manager.add_recommendation(
        context,
        Recommendation(source_agent="StrategyAgent", content="Expand through local partners", priority="high"),
    )

    summary = manager.get_summary(context)

    assert summary == {
        "query": "Analyze EV expansion",
        "task_type": "business_analysis",
        "findings": 1,
        "risks": 1,
        "recommendations": 1,
        "agent_history": [],
    }


def test_output_parser_handles_bullets_and_json_like_text() -> None:
    """Ensure malformed and simple bullet output is converted into structured models."""
    findings = parse_findings("- category: market | content: India EV market growing rapidly | confidence: 0.8\n- Fact two", source_agent="ResearchAgent")
    risks = parse_risks("```json\n[{\"description\": \"Battery shortages\", \"severity\": \"high\"}]\n```", source_agent="RiskAgent")
    recommendations = parse_recommendations("priority: high | content: Move fast", source_agent="StrategyAgent")

    assert findings[0].category == "market"
    assert findings[0].content == "India EV market growing rapidly"
    assert findings[1].content == "Fact two"
    assert risks[0].description == "Battery shortages"
    assert recommendations[0].priority == "high"


def test_workflow_result_schema_matches_structured_response() -> None:
    """Ensure the workflow result model exposes the phase 3 response shape."""
    result = WorkflowResult(
        query="Analyze EV expansion",
        task_type="business_analysis",
        agents_used=["ResearchAgent", "RiskAgent", "StrategyAgent"],
        findings=[Finding(source_agent="ResearchAgent", category="market", content="India EV growth", confidence=0.87)],
        risks=[Risk(source_agent="RiskAgent", description="Supply chain pressure", severity="high")],
        recommendations=[Recommendation(source_agent="StrategyAgent", content="Expand through local partners", priority="high")],
    )

    assert result.model_dump() == {
        "query": "Analyze EV expansion",
        "task_type": "business_analysis",
        "agents_used": ["ResearchAgent", "RiskAgent", "StrategyAgent"],
        "findings": [
            {
                "source_agent": "ResearchAgent",
                "category": "market",
                "content": "India EV growth",
                "confidence": 0.87,
            }
        ],
        "risks": [
            {
                "source_agent": "RiskAgent",
                "description": "Supply chain pressure",
                "severity": "high",
            }
        ],
        "recommendations": [
            {
                "source_agent": "StrategyAgent",
                "content": "Expand through local partners",
                "priority": "high",
            }
        ],
    }