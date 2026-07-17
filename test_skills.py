"""Test script for the Agent Skills feature."""

from skills.skill_manager import SkillManager
from skills.graph_integration import SkillGraphIntegration


def test_skills_initialization():
    """Test skill initialization from files."""
    print("Testing skills initialization...")
    skill_manager = SkillManager()
    success = skill_manager.initialize_skills()
    print(f"Skills initialization: {'SUCCESS' if success else 'FAILED'}")
    return success


def test_skill_loading():
    """Test loading skills from database."""
    print("\nTesting skill loading...")
    skill_manager = SkillManager()
    skill = skill_manager.load_skill("RiskAssessmentSkill")
    if skill:
        print(f"Loaded skill: {skill.skill_name}")
        print(f"Description: {skill.description}")
        return True
    else:
        print("Failed to load skill")
        return False


def test_skill_file_loading():
    """Test loading skill content from file."""
    print("\nTesting skill file loading...")
    skill_manager = SkillManager()
    content = skill_manager.load_skill_from_file("RiskAssessmentSkill")
    if content:
        print(f"Loaded skill content (length: {len(content)})")
        print(f"First 200 chars: {content[:200]}")
        return True
    else:
        print("Failed to load skill from file")
        return False


def test_skill_assignment():
    """Test assigning skills to an agent."""
    print("\nTesting skill assignment...")
    skill_manager = SkillManager()
    success = skill_manager.assign_skill("TestAgent", "RiskAssessmentSkill")
    print(f"Skill assignment: {'SUCCESS' if success else 'FAILED'}")
    return success


def test_default_skill_assignment():
    """Test assigning default skills based on task type."""
    print("\nTesting default skill assignment...")
    skill_manager = SkillManager()
    success = skill_manager.assign_default_skills("TestRiskAgent", "risk_analysis")
    print(f"Default skill assignment: {'SUCCESS' if success else 'FAILED'}")
    return success


def test_skill_context():
    """Test getting skill context for an agent."""
    print("\nTesting skill context retrieval...")
    skill_manager = SkillManager()
    context = skill_manager.get_skill_context("TestRiskAgent")
    if context:
        print(f"Skill context length: {len(context)}")
        print(f"First 300 chars: {context[:300]}")
        return True
    else:
        print("Failed to get skill context")
        return False


def test_graph_integration():
    """Test graph integration."""
    print("\nTesting graph integration...")
    graph_integration = SkillGraphIntegration()
    
    # Test creating skill node
    success = graph_integration.create_skill_node(
        "TestSkill",
        "A test skill for testing purposes",
        "skills/test_skill.md"
    )
    print(f"Skill node creation: {'SUCCESS' if success else 'FAILED'}")
    
    # Test creating agent-skill relationship
    success = graph_integration.create_agent_skill_relationship("TestAgent", "TestSkill")
    print(f"Agent-skill relationship: {'SUCCESS' if success else 'FAILED'}")
    
    # Test getting agent skills
    skills = graph_integration.get_agent_skills("TestAgent")
    print(f"Agent skills: {skills}")
    
    # Test getting skill stats
    stats = graph_integration.get_skill_stats()
    print(f"Skill stats: {stats}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Agent Skills Feature Test Suite")
    print("=" * 60)
    
    tests = [
        ("Skills Initialization", test_skills_initialization),
        ("Skill Loading", test_skill_loading),
        ("Skill File Loading", test_skill_file_loading),
        ("Skill Assignment", test_skill_assignment),
        ("Default Skill Assignment", test_default_skill_assignment),
        ("Skill Context", test_skill_context),
        ("Graph Integration", test_graph_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
