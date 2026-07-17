"""Agent generator for creating dynamic agent specifications."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from loguru import logger

from dynamic_agents.models import (
    AgentGenerationRequest,
    AgentGenerationResponse,
    AgentProfile,
)
from services.llm_service import LLMService, get_llm_service


class AgentGenerator:
    """Generates agent specifications using LLM-based synthesis."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        """Initialize the agent generator.

        Args:
            llm_service: LLM service for generation. If None, uses default.
        """
        self.llm_service = llm_service or get_llm_service()

    def generate_agent_profile(self, request: AgentGenerationRequest) -> AgentGenerationResponse:
        """Generate a complete agent profile based on task requirements.

        Args:
            request: Agent generation request with task and skill requirements.

        Returns:
            AgentGenerationResponse with generated profile and system prompt.
        """
        logger.info(
            "Generating agent profile for task type: {} with skills: {}",
            request.task_type,
            request.required_skills,
        )

        try:
            # Generate the agent specification
            prompt = self._build_generation_prompt(request)
            response = self.llm_service.generate(prompt)

            # Parse the JSON response
            agent_spec = json.loads(response)

            # Validate and create the profile
            profile = self._create_profile_from_spec(agent_spec, request)
            system_prompt = agent_spec.get("system_prompt", "")

            logger.info("Successfully generated agent profile: {}", profile.name)

            return AgentGenerationResponse(
                agent_profile=profile,
                system_prompt=system_prompt,
                success=True,
                error="",
            )
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse agent generation response: {}", exc)
            return AgentGenerationResponse(
                agent_profile=self._fallback_profile(request),
                system_prompt="",
                success=False,
                error=f"JSON parsing failed: {exc}",
            )
        except Exception as exc:
            logger.error("Agent generation failed: {}", exc)
            return AgentGenerationResponse(
                agent_profile=self._fallback_profile(request),
                system_prompt="",
                success=False,
                error=str(exc),
            )

    def generate_system_prompt(
        self,
        agent_name: str,
        agent_description: str,
        skills: list[str],
        task_type: str,
    ) -> str:
        """Generate a system prompt for an agent.

        Args:
            agent_name: Name of the agent.
            agent_description: Description of the agent's purpose.
            skills: List of agent skills.
            task_type: Primary task type the agent handles.

        Returns:
            Generated system prompt string.
        """
        prompt = f"""Generate a system prompt for an AI agent with the following characteristics:

Agent Name: {agent_name}
Description: {agent_description}
Skills: {', '.join(skills)}
Primary Task Type: {task_type}

The system prompt should:
1. Define the agent's role and purpose clearly
2. Specify the agent's responsibilities
3. Guide the agent on how to approach tasks
4. Be concise but comprehensive (2-4 paragraphs)

Return ONLY the system prompt text, no JSON or other formatting."""

        try:
            return self.llm_service.generate(prompt).strip()
        except Exception as exc:
            logger.error("Failed to generate system prompt: {}", exc)
            return self._fallback_system_prompt(agent_name, agent_description, skills)

    def generate_agent_definition(
        self,
        task_query: str,
        required_skills: list[str],
        task_type: str,
    ) -> tuple[AgentProfile, str]:
        """Generate a complete agent definition (profile and system prompt).

        Args:
            task_query: The task that requires this agent.
            required_skills: Skills the agent must have.
            task_type: Type of task the agent will handle.

        Returns:
            Tuple of (AgentProfile, system_prompt).
        """
        request = AgentGenerationRequest(
            task_query=task_query,
            required_skills=required_skills,
            task_type=task_type,
            context=f"Generated for task: {task_query}",
        )

        response = self.generate_agent_profile(request)

        if response.success:
            return response.agent_profile, response.system_prompt
        else:
            # Return fallback profile
            return response.agent_profile, self._fallback_system_prompt(
                response.agent_profile.name,
                response.agent_profile.description,
                response.agent_profile.skills,
            )

    def _build_generation_prompt(self, request: AgentGenerationRequest) -> str:
        """Build the LLM prompt for agent generation.

        Args:
            request: Agent generation request.

        Returns:
            Formatted prompt string.
        """
        skills_str = ", ".join(request.required_skills)

        prompt = f"""You are an expert AI agent designer. Create a specialized agent specification based on the following requirements:

Task Query: {request.task_query}
Required Skills: {skills_str}
Task Type: {request.task_type}
Context: {request.context}

Generate a JSON response with the following structure:
{{
    "name": "DescriptiveAgentName",
    "description": "A clear, concise description of what this agent does and its purpose",
    "skills": ["skill1", "skill2", "skill3"],
    "system_prompt": "A comprehensive system prompt that defines the agent's role, responsibilities, and approach to tasks. The prompt should be 2-4 paragraphs long and guide the agent on how to effectively use its skills to complete tasks of type {request.task_type}."
}}

CRITICAL GUIDELINES:
- Create REUSABLE DOMAIN AGENTS rather than narrow task-specific agents
- The agent name should be GENERAL and BROAD, not specific to the exact query
- DO NOT embed specific query wording into the agent name
- BAD: EVBatteryRiskAnalysisAgent, LithiumBatteryRiskAnalysisAgent, CarBatteryRiskAnalysisAgent
- GOOD: BatteryRiskAnalysisAgent, BatterySafetyAgent, RiskAnalysisAgent
- Use the core domain/skill as the name, not the specific application
- The description should be 1-2 sentences and describe the agent's general purpose
- Include all required skills in the skills array
- The system prompt should be practical and actionable
- Make the agent specialized for the DOMAIN, not the specific task instance

Return ONLY the JSON, no other text."""

        return prompt

    def _create_profile_from_spec(
        self, spec: dict[str, any], request: AgentGenerationRequest
    ) -> AgentProfile:
        """Create an AgentProfile from a generated specification.

        Args:
            spec: Generated agent specification dictionary.
            request: Original generation request.

        Returns:
            AgentProfile instance.
        """
        # Generate a unique agent ID
        agent_id = str(uuid.uuid4())

        # Extract fields with fallbacks
        name = spec.get("name", self._generate_agent_name(request.task_type))
        description = spec.get(
            "description",
            f"Specialized agent for {request.task_type} with skills: {', '.join(request.required_skills)}",
        )
        skills = spec.get("skills", request.required_skills)

        return AgentProfile(
            agent_id=agent_id,
            name=name,
            description=description,
            skills=skills,
            supported_task_types=[request.task_type],
            creation_source="dynamic",
            usage_count=0,
            created_at=datetime.utcnow(),
            is_dynamic=True,
        )

    def _generate_agent_name(self, task_type: str) -> str:
        """Generate a default agent name based on task type.

        Args:
            task_type: The task type.

        Returns:
            Generated agent name in CamelCase.
        """
        # Convert task_type to CamelCase
        words = task_type.replace("_", " ").replace("-", " ").split()
        camel_case = "".join(word.capitalize() for word in words)
        return f"{camel_case}Agent"

    def _fallback_profile(self, request: AgentGenerationRequest) -> AgentProfile:
        """Create a fallback profile when generation fails.

        Args:
            request: Original generation request.

        Returns:
            Basic AgentProfile.
        """
        return AgentProfile(
            agent_id=str(uuid.uuid4()),
            name=self._generate_agent_name(request.task_type),
            description=f"Specialized agent for {request.task_type}",
            skills=request.required_skills,
            supported_task_types=[request.task_type],
            creation_source="dynamic",
            usage_count=0,
            created_at=datetime.utcnow(),
            is_dynamic=True,
        )

    def _fallback_system_prompt(
        self, agent_name: str, description: str, skills: list[str]
    ) -> str:
        """Create a fallback system prompt.

        Args:
            agent_name: Name of the agent.
            description: Description of the agent.
            skills: List of skills.

        Returns:
            Basic system prompt.
        """
        skills_str = ", ".join(skills)
        return f"""You are {agent_name}, {description}.

Your core skills include: {skills_str}.

When completing tasks:
1. Analyze the request carefully to understand what is needed
2. Apply your specialized skills to address the specific requirements
3. Provide clear, actionable outputs
4. If information is missing, identify what additional context would be helpful

Focus on delivering high-quality results that leverage your expertise in {skills_str}."""
