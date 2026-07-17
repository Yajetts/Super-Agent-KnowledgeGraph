"""Test individual components of the evaluation framework."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.dataset_loader import DatasetLoader
from evaluation.metrics_multiagent import MetricsCalculator

print("Testing dataset loader...")
loader = DatasetLoader("evaluation/tasks.csv")
tasks = loader.load_tasks()
print(f"✓ Loaded {len(tasks)} tasks")
for task in tasks:
    print(f"  - {task.task_id}: {task.query}")

print("\nTesting metrics calculator...")
calculator = MetricsCalculator()

# Test coverage
test_text = """
This analysis covers market analysis, risks, opportunities, competitors, 
regulations, and provides actionable recommendations.
"""
coverage = calculator.calculate_coverage(test_text)
print(f"✓ Coverage score: {coverage:.3f}")

# Test risk counting
risk_text = """
Risks: Market volatility, regulatory changes, competitive pressure.
Major risk: Technology disruption.
Key risk: Supply chain issues.
"""
risk_count = calculator.count_risks(risk_text)
print(f"✓ Risk count: {risk_count}")

# Test recommendation counting
rec_text = """
Recommendations: Invest in R&D, expand to new markets.
Suggest: Partner with local firms.
Advise: Implement robust compliance.
Should: Monitor competitor activities.
Action: Launch pilot program.
"""
rec_count = calculator.count_recommendations(rec_text)
print(f"✓ Recommendation count: {rec_count}")

print("\n✓ All component tests passed!")
