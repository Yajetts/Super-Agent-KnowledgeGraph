"""Abstract base contract for all agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from services.llm_service import LLMService, get_llm_service
from superagent.task_context import TaskContext


class BaseAgent(ABC):
    """Define the shared contract that every agent must implement."""

    name: str = ""
    description: str = ""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or get_llm_service()

    @abstractmethod
    def execute(self, context: TaskContext) -> TaskContext:
        """Execute the agent workflow and return the updated context."""
        raise NotImplementedError
