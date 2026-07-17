"""Chain of Thought formatter for readable workflow execution narrative."""

from __future__ import annotations

from typing import Any


class ChainOfThought:
    """Format workflow execution into readable narrative sentences."""

    def __init__(self) -> None:
        """Initialize the chain of thought tracker."""
        self.thoughts: list[str] = []
        self.query: str = ""
        self.task_type: str = ""
        self.selected_agents: list[str] = []
        self.agent_scores: list[tuple[str, float]] = []
        self.agent_answers: dict[str, str] = {}
        self.execution_times: dict[str, float] = {}
        self.capability_gaps: list[str] = []
        self.dynamic_agents_created: list[str] = []

    def start_workflow(self, query: str) -> None:
        """Start tracking a new workflow."""
        self.query = query
        self.thoughts.append(f"The query is: '{query}'")

    def set_task_analysis(self, task_type: str, required_skills: list[str]) -> None:
        """Record task analysis results."""
        self.task_type = task_type
        skills_str = ", ".join(required_skills) if required_skills else "none specified"
        self.thoughts.append(f"I've analyzed this as a {task_type} task requiring skills: {skills_str}")

    def record_agent_selection(self, agents_with_scores: list[tuple[str, float]]) -> None:
        """Record which agents were selected with their relevance scores."""
        self.agent_scores = agents_with_scores
        self.selected_agents = [agent for agent, _ in agents_with_scores]
        
        if agents_with_scores:
            agents_info = []
            for agent, score in agents_with_scores:
                agents_info.append(f"{agent} (relevance: {score:.2f})")
            agents_str = ", ".join(agents_info)
            self.thoughts.append(f"Found {len(agents_with_scores)} relevant agents: {agents_str}")
        else:
            self.thoughts.append("No relevant agents found for this query")

    def record_capability_gaps(self, gaps: list[str]) -> None:
        """Record capability gaps detected."""
        self.capability_gaps = gaps
        if gaps:
            gaps_str = ", ".join(gaps)
            self.thoughts.append(f"Detected capability gaps for: {gaps_str}")

    def record_dynamic_agent_created(self, agent_name: str) -> None:
        """Record that a dynamic agent was created."""
        self.dynamic_agents_created.append(agent_name)
        self.thoughts.append(f"Created a new dynamic agent: {agent_name}")

    def record_agent_execution_start(self, agent_name: str) -> None:
        """Record that an agent started executing."""
        self.thoughts.append(f"Now executing {agent_name} agent")

    def record_agent_execution_complete(self, agent_name: str, answer: str, execution_time: float) -> None:
        """Record that an agent completed execution with its answer."""
        self.agent_answers[agent_name] = answer
        self.execution_times[agent_name] = execution_time
        
        # Truncate very long answers for readability
        display_answer = answer[:200] + "..." if len(answer) > 200 else answer
        self.thoughts.append(
            f"{agent_name} provided this answer: '{display_answer}' (completed in {execution_time:.2f}s)"
        )

    def record_context_retrieval(self, context_type: str, success: bool) -> None:
        """Record context retrieval results."""
        if success:
            self.thoughts.append(f"Successfully retrieved {context_type} context for additional information")
        else:
            self.thoughts.append(f"{context_type} context retrieval was not available, proceeding without it")

    def record_memory_storage(self, workflow_id: int) -> None:
        """Record that workflow was saved to memory."""
        self.thoughts.append(f"Saved this workflow to memory (ID: {workflow_id}) for future learning")

    def record_learning_processing(self, result: str) -> None:
        """Record learning pipeline processing."""
        self.thoughts.append(f"Learning pipeline processed this workflow: {result}")

    def get_narrative(self) -> str:
        """Get the complete chain of thought as a readable narrative."""
        if not self.thoughts:
            return "No chain of thought recorded."
        
        narrative = "\n".join(self.thoughts)
        return narrative

    def print_narrative(self) -> None:
        """Print the chain of thought narrative to console."""
        print("\n" + "=" * 80)
        print("CHAIN OF THOUGHT")
        print("=" * 80)
        print(self.get_narrative())
        print("=" * 80 + "\n")

    def clear(self) -> None:
        """Clear all recorded thoughts."""
        self.thoughts = []
        self.query = ""
        self.task_type = ""
        self.selected_agents = []
        self.agent_scores = []
        self.agent_answers = {}
        self.execution_times = {}
        self.capability_gaps = []
        self.dynamic_agents_created = []
