"""Generate task-level details with ASA and AUE scores."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def load_baseline_agents(results_path: str | Path) -> dict[str, list[str]]:
    """Load baseline agents from results CSV."""
    agents = {}
    with open(results_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row["task_id"]
            selected = json.loads(row["selected_agents"])
            agents[task_id] = selected
    return agents


def load_superagent_agents(results_path: str | Path) -> dict[str, list[str]]:
    """Load SuperAgent agents from results CSV."""
    agents = {}
    with open(results_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row["task_id"]
            selected = json.loads(row["selected_agents"])
            agents[task_id] = selected
    return agents


def load_expected_agents(mapping_path: str | Path) -> dict[str, list[str]]:
    """Load expected agent mappings from JSON."""
    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_asa(selected: list[str], expected: list[str]) -> float:
    """Calculate Agent Selection Accuracy."""
    if not expected:
        return 0.0
    selected_set = set(selected)
    expected_set = set(expected)
    correct = len(selected_set & expected_set)
    return correct / len(expected_set)


def calculate_saur(selected: list[str]) -> float:
    """Calculate Specialized Agent Utilization Rate."""
    if not selected:
        return 0.0
    # Core agents that are NOT specialized
    core_agents = {"ResearchAgent", "RiskAgent", "StrategyAgent"}
    specialized_count = sum(1 for agent in selected if agent not in core_agents)
    return specialized_count / len(selected)


def main() -> None:
    """Generate task details CSV."""
    # Load data
    superagent_agents = load_superagent_agents("evaluation/results/superagent_only_results.csv")
    expected_agents = load_expected_agents("evaluation/expected_agents.json")

    # Generate task details
    task_details = []
    for task_id in sorted(superagent_agents.keys()):
        selected = superagent_agents[task_id]
        expected = expected_agents.get(task_id, [])

        asa = calculate_asa(selected, expected)
        saur = calculate_saur(selected)

        task_details.append({
            "task_id": task_id,
            "expected_agents": ", ".join(expected),
            "selected_agents": ", ".join(selected),
            "asa_score": f"{asa:.2%}",
            "saur_score": f"{saur:.2%}",
        })

    # Save to CSV
    output_path = Path("evaluation/results/task_details_v2.csv")
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "expected_agents", "selected_agents", "asa_score", "saur_score"])
        writer.writeheader()
        writer.writerows(task_details)

    print(f"Task details saved to {output_path}")


if __name__ == "__main__":
    main()
