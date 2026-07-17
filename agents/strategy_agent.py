"""Strategy agent implementation."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from core.output_parser import parse_recommendations
from loguru import logger
from superagent.context_manager import ContextManager
from superagent.task_context import TaskContext


class StrategyAgent(BaseAgent):
    """Generate recommendations from prior findings."""

    name: str = "StrategyAgent"
    description: str = "Generates concise strategy recommendations."

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
        risk_context = "\n".join(
            f"- [{risk.severity}] {risk.description}" for risk in context.risks
        ) or "No risk findings yet."
        prompt = (
            "You are a strategic advisor.\n\n"
            "Consider both current analysis and historical recommendations from the knowledge graph and semantic search.\n"
            "The GraphRAG context provides both structural relationships and semantic similarity to historical recommendations.\n\n"
            "Review all findings and return a JSON array of recommendations. Each recommendation must include content and priority.\n\n"
            f"User query: {context.query}\n\n"
            f"Research findings:\n{research_context}\n\n"
            f"Risk findings:\n{risk_context}\n\n"
            f"GraphRAG context summary:\n{context_summary}"
        )
        response = self.llm_service.generate(prompt)
        recommendations = parse_recommendations(response, source_agent=self.name)
        context_manager = ContextManager()
        for recommendation in recommendations:
            context_manager.add_recommendation(context, recommendation)
        logger.info("{} updated context with {} recommendations", self.name, len(recommendations))
        return context
