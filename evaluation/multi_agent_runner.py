"""Multi-agent runner using existing specialized agents."""

from __future__ import annotations

import time

from agents.research_agent import ResearchAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from superagent.context_models import TaskContext


class MultiAgentRunner:
    """Run the specialized multi-agent system for evaluation."""

    def __init__(self) -> None:
        self.research_agent = ResearchAgent()
        self.risk_agent = RiskAgent()
        self.strategy_agent = StrategyAgent()

    def run(self, task: dict) -> dict:
        """Run multi-agent workflow on a task and return results."""
        query = task["query"]
        task_id = task["task_id"]

        # Initialize context
        context = TaskContext(
            query=query,
            task_type="decision_analysis",
        )

        start_time = time.time()

        # Execute agents in sequence
        context = self.research_agent.execute(context)
        research_output = self._format_findings(context.findings)

        context = self.risk_agent.execute(context)
        risk_output = self._format_risks(context.risks)

        context = self.strategy_agent.execute(context)
        strategy_output = self._format_recommendations(context.recommendations)

        execution_time = time.time() - start_time

        # Format final output
        final_output = self._format_final_output(
            research_output, risk_output, strategy_output
        )

        return {
            "task_id": task_id,
            "query": query,
            "research_output": research_output,
            "risk_output": risk_output,
            "strategy_output": strategy_output,
            "final_output": final_output,
            "execution_time": execution_time,
        }

    def _format_findings(self, findings: list) -> str:
        """Format findings as string."""
        if not findings:
            return "No research findings."
        return "\n".join(
            f"- [{finding.category}] {finding.content} (confidence: {finding.confidence:.2f})"
            for finding in findings
        )

    def _format_risks(self, risks: list) -> str:
        """Format risks as string."""
        if not risks:
            return "No risks identified."
        return "\n".join(
            f"- [{risk.severity}] {risk.description}" for risk in risks
        )

    def _format_recommendations(self, recommendations: list) -> str:
        """Format recommendations as string."""
        if not recommendations:
            return "No recommendations."
        return "\n".join(
            f"- [{rec.priority}] {rec.content}" for rec in recommendations
        )

    def _format_final_output(
        self, research_output: str, risk_output: str, strategy_output: str
    ) -> str:
        """Format final combined output."""
        return f"""# Research Findings
{research_output}

# Risks Identified
{risk_output}

# Strategic Recommendations
{strategy_output}
"""
