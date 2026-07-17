"""Risk agent implementation."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from core.output_parser import parse_risks
from loguru import logger
from superagent.context_manager import ContextManager
from superagent.context_models import Finding
from superagent.task_context import TaskContext


class RiskAgent(BaseAgent):
    """Assess risks using the query and research findings."""

    name: str = "RiskAgent"
    description: str = "Generates concise risk analysis findings."

    def execute(self, context: TaskContext) -> TaskContext:
        context.agent_history.append(self.name)
        
        # Use GraphRAG context if available, fall back to graph context
        if context.graphrag_context:
            context_summary = context.graphrag_context.context_summary
        elif context.graph_context:
            context_summary = context.graph_context.summary
        else:
            context_summary = "No historical context available."
        
        research_context = "\n".join(
            f"- [{finding.category}] {finding.content}" for finding in context.findings
        ) or "No research findings yet."
        prompt = (
            "You are a risk assessment specialist.\n\n"
            "Consider both current findings and relevant historical risks from the knowledge graph and semantic search.\n"
            "The GraphRAG context provides both structural relationships and semantic similarity to historical risks.\n\n"
            "Review the research findings and return a JSON array of risks. Each risk must include description and severity.\n\n"
            f"User query: {context.query}\n\n"
            f"Research findings:\n{research_context}\n\n"
            f"GraphRAG context summary:\n{context_summary}"
        )
        response = self.llm_service.generate(prompt)
        risks = parse_risks(response, source_agent=self.name)
        context_manager = ContextManager()
        for risk in risks:
            context_manager.add_risk(context, risk)
        logger.info("{} updated context with {} risks", self.name, len(risks))
        return context
