"""Metrics aggregation and statistical validation for agent comparison."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from scipy.stats import ttest_rel, wilcoxon


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a single agent system."""

    system_type: str
    average_coverage: float
    average_risks: float
    average_recommendations: float
    average_completeness: float
    average_execution_time: float
    average_recommendation_quality: float
    average_decision_support_quality: float


class MetricsAggregator:
    """Aggregate metrics and run statistical tests."""

    def __init__(self, results_dir: Path) -> None:
        self.results_dir = Path(results_dir)

    def aggregate_single_agent_metrics(self) -> AggregatedMetrics:
        """Aggregate metrics from single agent results."""
        df = pd.read_csv(self.results_dir / "single_agent_results.csv")
        return AggregatedMetrics(
            system_type="Single Agent",
            average_coverage=df["coverage"].mean(),
            average_risks=df["risk_count"].mean(),
            average_recommendations=df["recommendation_count"].mean(),
            average_completeness=df["completeness_score"].mean(),
            average_execution_time=df["execution_time"].mean(),
            average_recommendation_quality=df["recommendation_quality_score"].mean(),
            average_decision_support_quality=df["decision_support_quality_score"].mean(),
        )

    def aggregate_multi_agent_metrics(self) -> AggregatedMetrics:
        """Aggregate metrics from multi-agent results."""
        df = pd.read_csv(self.results_dir / "multi_agent_results.csv")
        return AggregatedMetrics(
            system_type="Multi-Agent",
            average_coverage=df["coverage"].mean(),
            average_risks=df["risk_count"].mean(),
            average_recommendations=df["recommendation_count"].mean(),
            average_completeness=df["completeness_score"].mean(),
            average_execution_time=df["execution_time"].mean(),
            average_recommendation_quality=df["recommendation_quality_score"].mean(),
            average_decision_support_quality=df["decision_support_quality_score"].mean(),
        )

    def save_aggregated_metrics(
        self, single_metrics: AggregatedMetrics, multi_metrics: AggregatedMetrics
    ) -> None:
        """Save aggregated metrics to CSV."""
        data = [
            {
                "system_type": single_metrics.system_type,
                "average_coverage": single_metrics.average_coverage,
                "average_risks": single_metrics.average_risks,
                "average_recommendations": single_metrics.average_recommendations,
                "average_completeness": single_metrics.average_completeness,
                "average_execution_time": single_metrics.average_execution_time,
                "average_recommendation_quality": single_metrics.average_recommendation_quality,
                "average_decision_support_quality": single_metrics.average_decision_support_quality,
            },
            {
                "system_type": multi_metrics.system_type,
                "average_coverage": multi_metrics.average_coverage,
                "average_risks": multi_metrics.average_risks,
                "average_recommendations": multi_metrics.average_recommendations,
                "average_completeness": multi_metrics.average_completeness,
                "average_execution_time": multi_metrics.average_execution_time,
                "average_recommendation_quality": multi_metrics.average_recommendation_quality,
                "average_decision_support_quality": multi_metrics.average_decision_support_quality,
            },
        ]
        df = pd.DataFrame(data)
        df.to_csv(self.results_dir / "specialized_agent_metrics.csv", index=False)

    def run_statistical_tests(self) -> dict:
        """Run statistical tests comparing single vs multi-agent systems."""
        single_df = pd.read_csv(self.results_dir / "single_agent_results.csv")
        multi_df = pd.read_csv(self.results_dir / "multi_agent_results.csv")

        results = {}

        # T-test for coverage
        try:
            t_stat_coverage, p_value_coverage = ttest_rel(
                multi_df["coverage"], single_df["coverage"]
            )
            results["coverage_t_stat"] = t_stat_coverage
            results["coverage_p_value"] = p_value_coverage
        except Exception:
            results["coverage_t_stat"] = None
            results["coverage_p_value"] = None

        # T-test for completeness
        try:
            t_stat_completeness, p_value_completeness = ttest_rel(
                multi_df["completeness_score"], single_df["completeness_score"]
            )
            results["completeness_t_stat"] = t_stat_completeness
            results["completeness_p_value"] = p_value_completeness
        except Exception:
            results["completeness_t_stat"] = None
            results["completeness_p_value"] = None

        # T-test for recommendation quality
        try:
            t_stat_rec_quality, p_value_rec_quality = ttest_rel(
                multi_df["recommendation_quality_score"], single_df["recommendation_quality_score"]
            )
            results["recommendation_quality_t_stat"] = t_stat_rec_quality
            results["recommendation_quality_p_value"] = p_value_rec_quality
        except Exception:
            results["recommendation_quality_t_stat"] = None
            results["recommendation_quality_p_value"] = None

        # T-test for decision support quality
        try:
            t_stat_decision_quality, p_value_decision_quality = ttest_rel(
                multi_df["decision_support_quality_score"], single_df["decision_support_quality_score"]
            )
            results["decision_support_quality_t_stat"] = t_stat_decision_quality
            results["decision_support_quality_p_value"] = p_value_decision_quality
        except Exception:
            results["decision_support_quality_t_stat"] = None
            results["decision_support_quality_p_value"] = None

        # Wilcoxon test for coverage (non-parametric alternative)
        try:
            w_stat_coverage, p_value_w_coverage = wilcoxon(
                multi_df["coverage"], single_df["coverage"]
            )
            results["coverage_wilcoxon_stat"] = w_stat_coverage
            results["coverage_wilcoxon_p_value"] = p_value_w_coverage
        except Exception:
            results["coverage_wilcoxon_stat"] = None
            results["coverage_wilcoxon_p_value"] = None

        # Wilcoxon test for completeness
        try:
            w_stat_completeness, p_value_w_completeness = wilcoxon(
                multi_df["completeness_score"], single_df["completeness_score"]
            )
            results["completeness_wilcoxon_stat"] = w_stat_completeness
            results["completeness_wilcoxon_p_value"] = p_value_w_completeness
        except Exception:
            results["completeness_wilcoxon_stat"] = None
            results["completeness_wilcoxon_p_value"] = None

        # Wilcoxon test for recommendation quality
        try:
            w_stat_rec_quality, p_value_w_rec_quality = wilcoxon(
                multi_df["recommendation_quality_score"], single_df["recommendation_quality_score"]
            )
            results["recommendation_quality_wilcoxon_stat"] = w_stat_rec_quality
            results["recommendation_quality_wilcoxon_p_value"] = p_value_w_rec_quality
        except Exception:
            results["recommendation_quality_wilcoxon_stat"] = None
            results["recommendation_quality_wilcoxon_p_value"] = None

        # Wilcoxon test for decision support quality
        try:
            w_stat_decision_quality, p_value_w_decision_quality = wilcoxon(
                multi_df["decision_support_quality_score"], single_df["decision_support_quality_score"]
            )
            results["decision_support_quality_wilcoxon_stat"] = w_stat_decision_quality
            results["decision_support_quality_wilcoxon_p_value"] = p_value_w_decision_quality
        except Exception:
            results["decision_support_quality_wilcoxon_stat"] = None
            results["decision_support_quality_wilcoxon_p_value"] = None

        # Save statistical analysis results
        stat_df = pd.DataFrame([results])
        stat_df.to_csv(self.results_dir / "statistical_analysis.csv", index=False)

        return results
