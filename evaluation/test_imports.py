"""Test imports for the evaluation framework."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Testing evaluation framework imports...")

try:
    from evaluation.dataset_loader import DatasetLoader, EvaluationTask
    print("✓ dataset_loader imports successful")
except Exception as e:
    print(f"✗ dataset_loader import failed: {e}")
    sys.exit(1)

try:
    from evaluation.single_agent_runner import SingleAgentRunner
    print("✓ single_agent_runner imports successful")
except Exception as e:
    print(f"✗ single_agent_runner import failed: {e}")
    sys.exit(1)

try:
    from evaluation.multi_agent_runner import MultiAgentRunner
    print("✓ multi_agent_runner imports successful")
except Exception as e:
    print(f"✗ multi_agent_runner import failed: {e}")
    sys.exit(1)

try:
    from evaluation.metrics_multiagent import MetricsCalculator
    print("✓ metrics_multiagent imports successful")
except Exception as e:
    print(f"✗ metrics_multiagent import failed: {e}")
    sys.exit(1)

try:
    from evaluation.llm_judge import LLMJudge
    print("✓ llm_judge imports successful")
except Exception as e:
    print(f"✗ llm_judge import failed: {e}")
    sys.exit(1)

try:
    from evaluation.metrics_aggregation import MetricsAggregator
    print("✓ metrics_aggregation imports successful")
except Exception as e:
    print(f"✗ metrics_aggregation import failed: {e}")
    sys.exit(1)

try:
    from evaluation.visualization import Visualizer
    print("✓ visualization imports successful")
except Exception as e:
    print(f"✗ visualization import failed: {e}")
    sys.exit(1)

try:
    from evaluation.specialized_report_generator import SpecializedReportGenerator
    print("✓ specialized_report_generator imports successful")
except Exception as e:
    print(f"✗ specialized_report_generator import failed: {e}")
    sys.exit(1)

try:
    from evaluation.runner import EvaluationRunner
    print("✓ runner imports successful")
except Exception as e:
    print(f"✗ runner import failed: {e}")
    sys.exit(1)

print("\n✓ All imports successful!")
