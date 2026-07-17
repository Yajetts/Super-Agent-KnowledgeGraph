"""Single agent runner for baseline evaluation."""

from __future__ import annotations

import time

from services.llm_service import get_llm_service


class SingleAgentRunner:
    """Run a single generic LLM agent for baseline evaluation."""

    def __init__(self) -> None:
        self.llm_service = get_llm_service()

    def run(self, task: dict) -> dict:
        """Run single agent on a task and return results."""
        query = task["query"]
        task_id = task["task_id"]

        prompt = (
            "You are a strategic decision-support assistant.\n\n"
            "Analyze the following request and provide a comprehensive response that includes:\n"
            "- Market analysis\n"
            "- Risks\n"
            "- Opportunities\n"
            "- Competitors\n"
            "- Regulations\n"
            "- Actionable recommendations\n\n"
            f"User query: {query}\n\n"
            "Provide a detailed, well-structured response."
        )

        start_time = time.time()
        response = self.llm_service.generate(prompt)
        execution_time = time.time() - start_time

        return {
            "task_id": task_id,
            "query": query,
            "response": response,
            "execution_time": execution_time,
        }
