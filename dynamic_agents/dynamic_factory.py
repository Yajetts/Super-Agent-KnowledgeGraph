"""Factory functions for creating and managing dynamic agents."""

from __future__ import annotations

from loguru import logger

from dynamic_agents.agent_generator import AgentGenerator
from dynamic_agents.agent_registry import DynamicAgentRegistry
from dynamic_agents.capability_analyzer import CapabilityAnalyzer
from dynamic_agents.deduplication import AgentDeduplicator
from dynamic_agents.graph_integration import DynamicAgentGraphIntegration
from dynamic_agents.memory_integration import DynamicAgentMemoryIntegration
from dynamic_agents.models import AgentProfile, AgentGenerationRequest
from dynamic_agents.repository import DynamicAgentRepository


def create_dynamic_agent(
    task_query: str,
    required_skills: list[str],
    task_type: str,
    context: str = "",
) -> AgentProfile | None:
    """Create a new dynamic agent based on task requirements.

    This function implements the agent creation workflow:
    1. Check if an agent with similar capabilities already exists
    2. If not, generate a new agent specification
    3. Register the new agent in the registry
    4. Persist to the database
    5. Add to graph database
    6. Store creation event in memory

    Args:
        task_query: The task that requires the new agent.
        required_skills: Skills the agent must have.
        task_type: Type of task the agent will handle.
        context: Additional context for agent generation.

    Returns:
        AgentProfile if creation was successful, None otherwise.
    """
    logger.info(
        "Attempting to create dynamic agent for task type: {} with skills: {}",
        task_type,
        required_skills,
    )

    # Initialize components
    registry = DynamicAgentRegistry()
    generator = AgentGenerator()
    deduplicator = AgentDeduplicator()
    graph_integration = DynamicAgentGraphIntegration()
    memory_integration = DynamicAgentMemoryIntegration()
    
    # Import SkillManager lazily to avoid circular import
    from skills.skill_manager import SkillManager
    skill_manager = SkillManager()

    # Step 1: Generate a tentative agent profile first
    request = AgentGenerationRequest(
        task_query=task_query,
        required_skills=required_skills,
        task_type=task_type,
        context=context,
    )

    response = generator.generate_agent_profile(request)

    if not response.success:
        logger.error("Failed to generate agent profile: {}", response.error)
        return None

    tentative_profile = response.agent_profile

    # Step 2: Check for duplicate agents using deduplication
    should_create, existing_agent = deduplicator.should_create_agent(tentative_profile)

    if not should_create and existing_agent:
        logger.info(
            "Reusing existing agent {} instead of creating new agent {}",
            existing_agent["name"],
            tentative_profile.name,
        )
        # Return the existing agent's profile
        return registry.get_agent_profile(existing_agent["name"])

    profile = tentative_profile

    # Step 3: Store system prompt in repository
    repository = DynamicAgentRepository()
    repository.save_agent(profile)
    repository.update_system_prompt(profile.name, response.system_prompt)

    # Step 4: Register in the registry
    success = registry.register_agent(profile)

    if success:
        logger.info("Successfully created and registered dynamic agent: {}", profile.name)

        # Step 5: Assign default skills based on task type
        try:
            skill_manager.assign_default_skills(profile.name, task_type)
            logger.info("Successfully assigned default skills to agent: {}", profile.name)
        except Exception as exc:
            logger.warning("Failed to assign default skills to agent {}: {}", profile.name, exc)

        # Step 6: Add to graph database
        try:
            graph_integration.register_agent_creation_event(profile, task_query, task_type)
            logger.info("Successfully added agent to graph: {}", profile.name)
        except Exception as exc:
            logger.warning("Failed to add agent to graph: {}", exc)

        # Step 7: Store creation event in memory
        try:
            memory_integration.store_agent_creation_event(profile, task_query, task_type, required_skills)
            logger.info("Successfully stored agent creation event in memory: {}", profile.name)
        except Exception as exc:
            logger.warning("Failed to store agent creation event in memory: {}", exc)

        return profile
    else:
        logger.warning("Agent generated but registration failed: {}", profile.name)
        return profile


def load_dynamic_agent(agent_name: str) -> AgentProfile | None:
    """Load a dynamic agent by name from the registry.

    Args:
        agent_name: Name of the agent to load.

    Returns:
        AgentProfile if found, None otherwise.
    """
    logger.debug("Loading dynamic agent: {}", agent_name)

    registry = DynamicAgentRegistry()
    profile = registry.get_agent_profile(agent_name)

    if profile:
        logger.info("Successfully loaded dynamic agent: {}", agent_name)
    else:
        logger.warning("Dynamic agent not found: {}", agent_name)

    return profile


def register_dynamic_agent(profile: AgentProfile) -> bool:
    """Register an existing agent profile in the registry and database.

    Args:
        profile: Agent profile to register.

    Returns:
        True if registration was successful, False otherwise.
    """
    logger.info("Registering dynamic agent: {}", profile.name)

    registry = DynamicAgentRegistry()
    repository = DynamicAgentRepository()

    # Save to database
    db_success = repository.save_agent(profile)

    # Register in memory
    registry_success = registry.register_agent(profile)

    if db_success and registry_success:
        logger.info("Successfully registered dynamic agent: {}", profile.name)
        return True
    else:
        logger.warning("Partial registration for agent: {}", profile.name)
        return registry_success  # Return True if at least in-memory registration succeeded


def analyze_and_create_if_needed(task_query: str) -> AgentProfile | None:
    """Analyze a task and create a dynamic agent if capability gaps are detected.

    This function implements the complete agent creation workflow:
    1. Analyze task requirements
    2. Identify required skills
    3. Check for capability gaps
    4. Create agent if gaps exist and coverage is below threshold

    Args:
        task_query: The task to analyze.

    Returns:
        AgentProfile if a new agent was created, None if no agent was needed.
    """
    logger.info("Analyzing task for potential agent creation: {}", task_query)

    # Step 1: Analyze task
    analyzer = CapabilityAnalyzer()
    analysis = analyzer.analyze_task(task_query)

    logger.info(
        "Task analysis - Type: {}, Coverage: {:.2f}, Should create: {}",
        analysis.task_type,
        analysis.coverage_score,
        analysis.should_create_agent,
    )

    # Step 2: Check if agent creation is recommended
    if not analysis.should_create_agent:
        logger.info("No agent creation needed, existing agents provide sufficient coverage")
        return None

    # Step 3: Create the agent
    profile = create_dynamic_agent(
        task_query=task_query,
        required_skills=analysis.required_skills,
        task_type=analysis.task_type,
        context=f"Created for task: {task_query}",
    )

    return profile


def _find_similar_agent(
    registry: DynamicAgentRegistry, required_skills: list[str], task_type: str
) -> AgentProfile | None:
    """Find an existing agent with similar capabilities.

    Args:
        registry: Agent registry to search.
        required_skills: Skills required for the task.
        task_type: Type of task.

    Returns:
        AgentProfile if a similar agent is found, None otherwise.
    """
    # Check for agents that support the task type
    agents_by_task = registry.find_agents_by_task_type(task_type)

    if agents_by_task:
        # Check if any of these agents have the required skills
        for agent_dict in agents_by_task:
            agent_skills = agent_dict.get("skills", [])
            # Check if all required skills are covered
            if all(skill in agent_skills for skill in required_skills):
                profile = registry.get_agent_profile(agent_dict["name"])
                if profile:
                    return profile

    # Check for agents with matching skills regardless of task type
    for skill in required_skills:
        agents_by_skill = registry.find_agents_by_skill(skill)
        if agents_by_skill:
            for agent_dict in agents_by_skill:
                agent_skills = agent_dict.get("skills", [])
                # Check if this agent covers most of the required skills
                coverage = sum(1 for s in required_skills if s in agent_skills) / len(
                    required_skills
                )
                if coverage >= 0.8:  # 80% skill coverage threshold
                    profile = registry.get_agent_profile(agent_dict["name"])
                    if profile:
                        logger.info(
                            "Found agent {} with {:.0f}% skill coverage",
                            profile.name,
                            coverage * 100,
                        )
                        return profile

    return None
