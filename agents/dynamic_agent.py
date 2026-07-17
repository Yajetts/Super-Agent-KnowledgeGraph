"""Dynamic agent implementation that extends BaseAgent."""

from __future__ import annotations

from loguru import logger

from agents.base_agent import BaseAgent
from core.output_parser import parse_findings, parse_risks, parse_recommendations
from dynamic_agents.agent_registry import DynamicAgentRegistry
from dynamic_agents.repository import DynamicAgentRepository
from services.llm_service import LLMService, get_llm_service
from superagent.context_manager import ContextManager
from superagent.task_context import TaskContext


class DynamicAgent(BaseAgent):
    """Runtime dynamic agent that behaves like a normal agent."""

    name: str = ""
    description: str = ""
    skills: list[str] = []
    system_prompt: str = ""

    def __init__(
        self,
        agent_name: str,
        llm_service: LLMService | None = None,
    ) -> None:
        """Initialize a dynamic agent by loading its profile.

        Args:
            agent_name: Name of the dynamic agent to load.
            llm_service: LLM service. If None, uses default.
        """
        super().__init__(llm_service)
        self.name = agent_name

        # Load agent profile
        registry = DynamicAgentRegistry()
        profile = registry.get_agent_profile(agent_name)

        if not profile:
            raise ValueError(f"Dynamic agent not found: {agent_name}")

        self.description = profile.description
        self.skills = profile.skills
        self._profile = profile

        # Load system prompt from repository
        repository = DynamicAgentRepository()
        self.system_prompt = repository.get_system_prompt(agent_name) or ""

        if not self.system_prompt:
            logger.warning("No system prompt found for dynamic agent: {}", agent_name)

    def execute(self, context: TaskContext) -> TaskContext:
        """Execute the agent workflow and return the updated context.

        Args:
            context: Current task context.

        Returns:
            Updated task context with agent results.
        """
        logger.info("Executing dynamic agent: {}", self.name)

        # Add to agent history
        context.agent_history.append(self.name)

        # Update usage count
        registry = DynamicAgentRegistry()
        registry.update_usage_count(self.name)

        # Build the execution prompt
        prompt = self._build_execution_prompt(context)

        try:
            # Generate response using LLM
            response = self.llm_service.generate(prompt)

            # Parse response into structured outputs
            context_manager = ContextManager()

            # Try to parse as findings
            try:
                findings = parse_findings(response, source_agent=self.name)
                for finding in findings:
                    context_manager.add_finding(context, finding)
                logger.info("Dynamic agent {} added {} findings", self.name, len(findings))
            except Exception as exc:
                logger.debug("Failed to parse findings from response: {}", exc)

            # Try to parse as risks
            try:
                risks = parse_risks(response, source_agent=self.name)
                for risk in risks:
                    context_manager.add_risk(context, risk)
                logger.info("Dynamic agent {} added {} risks", self.name, len(risks))
            except Exception as exc:
                logger.debug("Failed to parse risks from response: {}", exc)

            # Try to parse as recommendations
            try:
                recommendations = parse_recommendations(response, source_agent=self.name)
                for recommendation in recommendations:
                    context_manager.add_recommendation(context, recommendation)
                logger.info("Dynamic agent {} added {} recommendations", self.name, len(recommendations))
            except Exception as exc:
                logger.debug("Failed to parse recommendations from response: {}", exc)

            # If no structured outputs were parsed, add as a finding with the raw response
            if not context.findings and not context.risks and not context.recommendations:
                from superagent.context_models import Finding
                finding = Finding(
                    source_agent=self.name,
                    category="general",
                    content=response,
                    confidence=0.5,
                )
                context_manager.add_finding(context, finding)
                logger.info("Dynamic agent {} added raw response as finding", self.name)

            # Record skill usage metrics
            try:
                from skills.skill_manager import SkillManager
                skill_manager = SkillManager()
                skills = skill_manager.load_agent_skills(self.name)
                for skill in skills:
                    skill_manager.record_skill_usage(skill.skill_id, success=True)
                logger.debug("Recorded skill usage for agent {}", self.name)
            except Exception as exc:
                logger.warning("Failed to record skill usage for agent {}: {}", self.name, exc)

            logger.info("Dynamic agent {} completed successfully", self.name)
            return context

        except Exception as exc:
            logger.error("Dynamic agent {} execution failed: {}", self.name, exc)
            # Add error as a finding
            from superagent.context_models import Finding
            context_manager = ContextManager()
            error_finding = Finding(
                source_agent=self.name,
                category="error",
                content=f"Dynamic agent {self.name} failed: {exc}",
                confidence=1.0,
            )
            context_manager.add_finding(context, error_finding)

            # Record skill usage metrics (with failure)
            try:
                from skills.skill_manager import SkillManager
                skill_manager = SkillManager()
                skills = skill_manager.load_agent_skills(self.name)
                for skill in skills:
                    skill_manager.record_skill_usage(skill.skill_id, success=False)
                logger.debug("Recorded skill usage (failure) for agent {}", self.name)
            except Exception as exc2:
                logger.warning("Failed to record skill usage for agent {}: {}", self.name, exc2)

            return context

    def _build_execution_prompt(self, context: TaskContext) -> str:
        """Build the execution prompt for the LLM.

        Args:
            context: Current task context.

        Returns:
            Formatted prompt string.
        """
        # Start with system prompt
        prompt_parts = [self.system_prompt]

        # Load and inject skill context
        try:
            from skills.skill_manager import SkillManager
            skill_manager = SkillManager()
            skill_context = skill_manager.get_skill_context(self.name)
            if skill_context:
                prompt_parts.append(skill_context)
                logger.debug("Injected skill context for agent: {}", self.name)
        except Exception as exc:
            logger.warning("Failed to load skill context for agent {}: {}", self.name, exc)

        # Add task context
        if context.query:
            prompt_parts.append(f"\nTask: {context.query}")

        # Add previous agent history if available
        if context.agent_history:
            prompt_parts.append(f"\nPrevious agents executed: {', '.join(context.agent_history)}")

        # Add existing findings if available
        if context.findings:
            prompt_parts.append("\nExisting findings:")
            for finding in context.findings:
                prompt_parts.append(f"\n- [{finding.category}] {finding.content} (confidence: {finding.confidence})")

        # Add existing risks if available
        if context.risks:
            prompt_parts.append("\nExisting risks:")
            for risk in context.risks:
                prompt_parts.append(f"\n- [{risk.severity}] {risk.description}")

        # Add existing recommendations if available
        if context.recommendations:
            prompt_parts.append("\nExisting recommendations:")
            for rec in context.recommendations:
                prompt_parts.append(f"\n- [{rec.priority}] {rec.content}")

        # Add any additional context
        if context.metadata:
            prompt_parts.append(f"\nAdditional context: {context.metadata}")

        return "\n".join(prompt_parts)

    @classmethod
    def create_from_profile(
        cls,
        agent_name: str,
        description: str,
        skills: list[str],
        system_prompt: str,
        llm_service: LLMService | None = None,
    ) -> DynamicAgent:
        """Create a DynamicAgent instance directly from profile data.

        This is useful for testing or when you have the profile data already loaded.

        Args:
            agent_name: Name of the agent.
            description: Agent description.
            skills: List of agent skills.
            system_prompt: System prompt for the agent.
            llm_service: LLM service. If None, uses default.

        Returns:
            DynamicAgent instance.
        """
        agent = cls.__new__(cls)
        BaseAgent.__init__(agent, llm_service or get_llm_service())
        agent.name = agent_name
        agent.description = description
        agent.skills = skills
        agent.system_prompt = system_prompt
        return agent
