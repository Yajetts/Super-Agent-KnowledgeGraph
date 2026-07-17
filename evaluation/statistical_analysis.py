"""Statistical significance analysis for SuperAgent evaluation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy import stats


def load_results(csv_path: Path) -> dict[str, dict]:
    """Load results from CSV."""
    results = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row["task_id"]
            results[task_id] = {
                "selected_agents": json.loads(row["selected_agents"]),
                "execution_time": float(row["execution_time"]),
            }
    return results


def load_expected_agents(json_path: Path) -> dict[str, list[str]]:
    """Load expected agent mappings."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_per_task_asa(results: dict, expected_agents: dict) -> dict[str, float]:
    """Calculate per-task Agent Selection Accuracy."""
    per_task_asa = {}
    for task_id, data in results.items():
        selected = set(data["selected_agents"])
        expected = set(expected_agents.get(task_id, []))
        if expected:
            asa = len(selected & expected) / len(expected)
        else:
            asa = 0.0
        per_task_asa[task_id] = asa
    return per_task_asa


def calculate_per_task_saur(results: dict) -> dict[str, float]:
    """Calculate per-task Specialized Agent Utilization Rate."""
    core_agents = {"ResearchAgent", "RiskAgent", "StrategyAgent"}
    per_task_saur = {}
    for task_id, data in results.items():
        selected = data["selected_agents"]
        if selected:
            specialized_count = sum(1 for agent in selected if agent not in core_agents)
            saur = specialized_count / len(selected)
        else:
            saur = 0.0
        per_task_saur[task_id] = saur
    return per_task_saur


def calculate_per_task_execution_time(results: dict) -> dict[str, float]:
    """Extract per-task execution times."""
    return {task_id: data["execution_time"] for task_id, data in results.items()}


def perform_wilcoxon_test(baseline_values: list[float], superagent_values: list[float]) -> dict:
    """Perform Wilcoxon signed-rank test for paired samples."""
    # Ensure same order by task_id
    baseline_arr = np.array(baseline_values)
    superagent_arr = np.array(superagent_values)
    
    # Wilcoxon signed-rank test
    statistic, p_value = stats.wilcoxon(baseline_arr, superagent_arr, alternative='less')
    
    return {
        "statistic": statistic,
        "p_value": p_value,
        "baseline_mean": np.mean(baseline_arr),
        "superagent_mean": np.mean(superagent_arr),
        "baseline_std": np.std(baseline_arr, ddof=1),
        "superagent_std": np.std(superagent_arr, ddof=1),
    }


def perform_paired_ttest(baseline_values: list[float], superagent_values: list[float]) -> dict:
    """Perform paired t-test."""
    baseline_arr = np.array(baseline_values)
    superagent_arr = np.array(superagent_values)
    
    statistic, p_value = stats.ttest_rel(baseline_arr, superagent_arr, alternative='less')
    
    return {
        "statistic": statistic,
        "p_value": p_value,
        "baseline_mean": np.mean(baseline_arr),
        "superagent_mean": np.mean(superagent_arr),
        "baseline_std": np.std(baseline_arr, ddof=1),
        "superagent_std": np.std(superagent_arr, ddof=1),
    }


def main() -> None:
    """Run statistical analysis."""
    import csv
    
    print("=" * 60)
    print("Statistical Significance Analysis")
    print("=" * 60)
    print()
    
    # Load data
    baseline_results = load_results(Path("evaluation/results/baseline_results.csv"))
    superagent_results = load_results(Path("evaluation/results/superagent_only_results.csv"))
    expected_agents = load_expected_agents(Path("evaluation/expected_agents.json"))
    
    # Get task IDs in consistent order
    task_ids = sorted(baseline_results.keys())
    
    # Calculate per-task metrics
    baseline_asa = calculate_per_task_asa(baseline_results, expected_agents)
    superagent_asa = calculate_per_task_asa(superagent_results, expected_agents)
    
    baseline_saur = calculate_per_task_saur(baseline_results)
    superagent_saur = calculate_per_task_saur(superagent_results)
    
    baseline_time = calculate_per_task_execution_time(baseline_results)
    superagent_time = calculate_per_task_execution_time(superagent_results)
    
    # Extract values in consistent order
    baseline_asa_values = [baseline_asa[tid] for tid in task_ids]
    superagent_asa_values = [superagent_asa[tid] for tid in task_ids]
    
    baseline_saur_values = [baseline_saur[tid] for tid in task_ids]
    superagent_saur_values = [superagent_saur[tid] for tid in task_ids]
    
    baseline_time_values = [baseline_time[tid] for tid in task_ids]
    superagent_time_values = [superagent_time[tid] for tid in task_ids]
    
    print("Per-task metrics:")
    print(f"{'Task':<6} {'Baseline ASA':<15} {'SuperAgent ASA':<15} {'Baseline SAUR':<15} {'SuperAgent SAUR':<15}")
    for tid in task_ids:
        print(f"{tid:<6} {baseline_asa[tid]:<15.4f} {superagent_asa[tid]:<15.4f} {baseline_saur[tid]:<15.4f} {superagent_saur[tid]:<15.4f}")
    print()
    
    # Perform statistical tests
    print("Statistical Tests (Wilcoxon Signed-Rank Test)")
    print("-" * 60)
    
    # ASA test (testing if SuperAgent > Baseline, so alternative='greater' for SuperAgent)
    asa_result = stats.wilcoxon(baseline_asa_values, superagent_asa_values, alternative='less')
    print(f"\nAgent Selection Accuracy (ASA):")
    print(f"  Baseline:  {np.mean(baseline_asa_values):.4f} (±{np.std(baseline_asa_values, ddof=1):.4f})")
    print(f"  SuperAgent: {np.mean(superagent_asa_values):.4f} (±{np.std(superagent_asa_values, ddof=1):.4f})")
    print(f"  Statistic: {asa_result.statistic}")
    print(f"  p-value: {asa_result.pvalue:.6f}")
    print(f"  Significant: {'Yes' if asa_result.pvalue < 0.05 else 'No'} (α=0.05)")
    
    # SAUR test
    saur_result = stats.wilcoxon(baseline_saur_values, superagent_saur_values, alternative='less')
    print(f"\nSpecialized Agent Utilization Rate (SAUR):")
    print(f"  Baseline:  {np.mean(baseline_saur_values):.4f} (±{np.std(baseline_saur_values, ddof=1):.4f})")
    print(f"  SuperAgent: {np.mean(superagent_saur_values):.4f} (±{np.std(superagent_saur_values, ddof=1):.4f})")
    print(f"  Statistic: {saur_result.statistic}")
    print(f"  p-value: {saur_result.pvalue:.6f}")
    print(f"  Significant: {'Yes' if saur_result.pvalue < 0.05 else 'No'} (α=0.05)")
    
    # Execution time test (testing if Baseline < SuperAgent, i.e., SuperAgent is slower)
    time_result = stats.wilcoxon(baseline_time_values, superagent_time_values, alternative='less')
    print(f"\nExecution Time:")
    print(f"  Baseline:  {np.mean(baseline_time_values):.4f}s (±{np.std(baseline_time_values, ddof=1):.4f})")
    print(f"  SuperAgent: {np.mean(superagent_time_values):.4f}s (±{np.std(superagent_time_values, ddof=1):.4f})")
    print(f"  Statistic: {time_result.statistic}")
    print(f"  p-value: {time_result.pvalue:.6f}")
    print(f"  Significant: {'Yes' if time_result.pvalue < 0.05 else 'No'} (α=0.05)")
    
    print()
    print("=" * 60)
    print("Statistical Analysis Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
