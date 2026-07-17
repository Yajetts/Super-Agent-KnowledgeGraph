"""Research agent implementation."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from core.output_parser import parse_findings
from loguru import logger
from superagent.context_manager import ContextManager
from superagent.task_context import TaskContext


class ResearchAgent(BaseAgent):
    """Generate research findings for the supplied query."""

    name: str = "ResearchAgent"
    description: str = "Generates concise research findings."

    def execute(self, context: TaskContext) -> TaskContext:
        context.agent_history.append(self.name)
        
        # Use GraphRAG context if available, fall back to graph context
        if context.graphrag_context:
            context_summary = context.graphrag_context.context_summary
        elif context.graph_context:
            context_summary = context.graph_context.summary
        else:
            context_summary = "No historical context available."
        
        prompt = (
            "You are a research analyst.\n\n"
            "You have access to historical knowledge retrieved from both a knowledge graph and semantic search.\n"
            "This combined context provides both structural relationships and semantic similarity.\n"
            "Use this information when relevant.\n"
            "Do not blindly repeat historical findings.\n"
            "Use them as supporting context.\n\n"
            "Analyze the user's request.\n\n"
            "Return a JSON array of findings. Each finding must include category, content, and confidence.\n\n"
            f"User query: {context.query}\n\n"
            f"GraphRAG context summary:\n{context_summary}"
        )
        response = self.llm_service.generate(prompt)
        findings = parse_findings(response, source_agent=self.name)
        context_manager = ContextManager()
        for finding in findings:
            context_manager.add_finding(context, finding)
        logger.info("{} updated context with {} findings", self.name, len(findings))
        return context
