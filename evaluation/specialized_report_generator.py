"""Report generator for specialized agent evaluation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class SpecializedReportGenerator:
    """Generate markdown report for agent comparison evaluation."""

    def __init__(self, results_dir: Path) -> None:
        self.results_dir = Path(results_dir)

    def generate_report(self, output_path: Path) -> None:
        """Generate the complete evaluation report."""
        # Load data
        tasks_df = pd.read_csv(self.results_dir.parent / "tasks.csv")
        single_df = pd.read_csv(self.results_dir / "single_agent_results.csv")
        multi_df = pd.read_csv(self.results_dir / "multi_agent_results.csv")
        metrics_df = pd.read_csv(self.results_dir / "specialized_agent_metrics.csv")
        
        # Try to load statistical analysis
        try:
            stat_df = pd.read_csv(self.results_dir / "statistical_analysis.csv")
            has_stats = True
        except FileNotFoundError:
            has_stats = False

        # Generate report
        report = self._build_report(
            tasks_df, single_df, multi_df, metrics_df, stat_df if has_stats else None
        )

        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"Report generated at {output_path}")

    def _build_report(
        self, tasks_df, single_df, multi_df, metrics_df, stat_df
    ) -> str:
        """Build the markdown report content."""
        report = "# Specialized Agent Evaluation Report\n\n"
        report += "## Overview\n\n"
        report += "This report compares the performance of a single general-purpose agent "
        report += "against a specialized multi-agent system (Research → Risk → Strategy) "
        report += "on decision-support tasks.\n\n"

        # Dataset size
        report += "## Dataset Size\n\n"
        report += f"- **Total Tasks**: {len(tasks_df)}\n"
        report += f"- **Task IDs**: {', '.join(tasks_df['task_id'].tolist())}\n\n"

        # Single agent results
        report += "## Single Agent Results\n\n"
        report += "### Metrics Summary\n\n"
        single_metrics = metrics_df[metrics_df["system_type"] == "Single Agent"].iloc[0]
        report += "| Metric | Value |\n"
        report += "|--------|-------|\n"
        report += f"| Average Coverage | {single_metrics['average_coverage']:.3f} |\n"
        report += f"| Average Risks Identified | {single_metrics['average_risks']:.1f} |\n"
        report += f"| Average Recommendations | {single_metrics['average_recommendations']:.1f} |\n"
        report += f"| Average Completeness Score | {single_metrics['average_completeness']:.2f} |\n"
        report += f"| Average Recommendation Quality | {single_metrics['average_recommendation_quality']:.2f} |\n"
        report += f"| Average Decision Support Quality | {single_metrics['average_decision_support_quality']:.2f} |\n"
        report += f"| Average Execution Time | {single_metrics['average_execution_time']:.2f}s |\n\n"

        report += "### Per-Task Results\n\n"
        report += "| Task ID | Coverage | Risks | Recommendations | Completeness | Rec Quality | Decision Quality | Time (s) |\n"
        report += "|---------|----------|-------|-----------------|---------------|-------------|-----------------|----------|\n"
        for _, row in single_df.iterrows():
            report += f"| {row['task_id']} | {row['coverage']:.3f} | {row['risk_count']} | "
            report += f"{row['recommendation_count']} | {row['completeness_score']:.2f} | "
            report += f"{row['recommendation_quality_score']:.2f} | {row['decision_support_quality_score']:.2f} | "
            report += f"{row['execution_time']:.2f} |\n"
        report += "\n"

        # Multi-agent results
        report += "## Multi-Agent Results\n\n"
        report += "### Metrics Summary\n\n"
        multi_metrics = metrics_df[metrics_df["system_type"] == "Multi-Agent"].iloc[0]
        report += "| Metric | Value |\n"
        report += "|--------|-------|\n"
        report += f"| Average Coverage | {multi_metrics['average_coverage']:.3f} |\n"
        report += f"| Average Risks Identified | {multi_metrics['average_risks']:.1f} |\n"
        report += f"| Average Recommendations | {multi_metrics['average_recommendations']:.1f} |\n"
        report += f"| Average Completeness Score | {multi_metrics['average_completeness']:.2f} |\n"
        report += f"| Average Recommendation Quality | {multi_metrics['average_recommendation_quality']:.2f} |\n"
        report += f"| Average Decision Support Quality | {multi_metrics['average_decision_support_quality']:.2f} |\n"
        report += f"| Average Execution Time | {multi_metrics['average_execution_time']:.2f}s |\n\n"

        report += "### Per-Task Results\n\n"
        report += "| Task ID | Coverage | Risks | Recommendations | Completeness | Rec Quality | Decision Quality | Time (s) |\n"
        report += "|---------|----------|-------|-----------------|---------------|-------------|-----------------|----------|\n"
        for _, row in multi_df.iterrows():
            report += f"| {row['task_id']} | {row['coverage']:.3f} | {row['risk_count']} | "
            report += f"{row['recommendation_count']} | {row['completeness_score']:.2f} | "
            report += f"{row['recommendation_quality_score']:.2f} | {row['decision_support_quality_score']:.2f} | "
            report += f"{row['execution_time']:.2f} |\n"
        report += "\n"

        # Statistical analysis
        if stat_df is not None:
            report += "## Statistical Analysis\n\n"
            report += "### T-Test Results\n\n"
            report += "| Metric | T-Statistic | P-Value |\n"
            report += "|--------|-------------|---------|\n"

            if "coverage_t_stat" in stat_df.columns:
                cov_t = stat_df["coverage_t_stat"].iloc[0]
                cov_p = stat_df["coverage_p_value"].iloc[0]
                report += f"| Coverage | {cov_t:.4f} | {cov_p:.4f} |\n"

            if "completeness_t_stat" in stat_df.columns:
                comp_t = stat_df["completeness_t_stat"].iloc[0]
                comp_p = stat_df["completeness_p_value"].iloc[0]
                report += f"| Completeness | {comp_t:.4f} | {comp_p:.4f} |\n"

            if "recommendation_quality_t_stat" in stat_df.columns:
                rec_t = stat_df["recommendation_quality_t_stat"].iloc[0]
                rec_p = stat_df["recommendation_quality_p_value"].iloc[0]
                report += f"| Recommendation Quality | {rec_t:.4f} | {rec_p:.4f} |\n"

            if "decision_support_quality_t_stat" in stat_df.columns:
                dec_t = stat_df["decision_support_quality_t_stat"].iloc[0]
                dec_p = stat_df["decision_support_quality_p_value"].iloc[0]
                report += f"| Decision Support Quality | {dec_t:.4f} | {dec_p:.4f} |\n"
            report += "\n"

            report += "### Wilcoxon Signed-Rank Test Results\n\n"
            report += "| Metric | Statistic | P-Value |\n"
            report += "|--------|-----------|---------|\n"

            if "coverage_wilcoxon_stat" in stat_df.columns:
                cov_w = stat_df["coverage_wilcoxon_stat"].iloc[0]
                cov_wp = stat_df["coverage_wilcoxon_p_value"].iloc[0]
                report += f"| Coverage | {cov_w:.4f} | {cov_wp:.4f} |\n"

            if "completeness_wilcoxon_stat" in stat_df.columns:
                comp_w = stat_df["completeness_wilcoxon_stat"].iloc[0]
                comp_wp = stat_df["completeness_wilcoxon_p_value"].iloc[0]
                report += f"| Completeness | {comp_w:.4f} | {comp_wp:.4f} |\n"

            if "recommendation_quality_wilcoxon_stat" in stat_df.columns:
                rec_w = stat_df["recommendation_quality_wilcoxon_stat"].iloc[0]
                rec_wp = stat_df["recommendation_quality_wilcoxon_p_value"].iloc[0]
                report += f"| Recommendation Quality | {rec_w:.4f} | {rec_wp:.4f} |\n"

            if "decision_support_quality_wilcoxon_stat" in stat_df.columns:
                dec_w = stat_df["decision_support_quality_wilcoxon_stat"].iloc[0]
                dec_wp = stat_df["decision_support_quality_wilcoxon_p_value"].iloc[0]
                report += f"| Decision Support Quality | {dec_w:.4f} | {dec_wp:.4f} |\n"
            report += "\n"

        # Recommendation Quality section
        report += "## Recommendation Quality\n\n"
        report += f"**Single Agent Average**: {single_metrics['average_recommendation_quality']:.2f}/10\n\n"
        report += f"**Multi-Agent Average**: {multi_metrics['average_recommendation_quality']:.2f}/10\n\n"
        rec_quality_diff = multi_metrics["average_recommendation_quality"] - single_metrics["average_recommendation_quality"]
        if rec_quality_diff > 0:
            report += f"The multi-agent system achieved {rec_quality_diff:.2f} points higher recommendation quality. "
        else:
            report += f"The single agent achieved {abs(rec_quality_diff):.2f} points higher recommendation quality. "
        report += "This metric evaluates actionability, specificity, feasibility, and strategic value of recommendations.\n\n"

        # Decision Support Quality section
        report += "## Decision Support Quality\n\n"
        report += f"**Single Agent Average**: {single_metrics['average_decision_support_quality']:.2f}/10\n\n"
        report += f"**Multi-Agent Average**: {multi_metrics['average_decision_support_quality']:.2f}/10\n\n"
        decision_quality_diff = multi_metrics["average_decision_support_quality"] - single_metrics["average_decision_support_quality"]
        if decision_quality_diff > 0:
            report += f"The multi-agent system achieved {decision_quality_diff:.2f} points higher decision support quality. "
        else:
            report += f"The single agent achieved {abs(decision_quality_diff):.2f} points higher decision support quality. "
        report += "This metric evaluates analytical depth, risk awareness, evidence, strategic insight, and decision usefulness.\n\n"

        # Key findings
        report += "## Key Findings\n\n"
        report += self._generate_key_findings(single_metrics, multi_metrics, stat_df)

        # Charts reference
        report += "## Visualizations\n\n"
        report += "Comparison charts have been generated in the `results/charts/` directory:\n\n"
        report += "- `coverage_comparison.png`\n"
        report += "- `risks_comparison.png`\n"
        report += "- `recommendations_comparison.png`\n"
        report += "- `completeness_comparison.png`\n"
        report += "- `execution_time_comparison.png`\n\n"

        return report

    def _generate_key_findings(self, single_metrics, multi_metrics, stat_df) -> str:
        """Generate key findings section."""
        findings = ""

        # Coverage comparison
        cov_diff = multi_metrics["average_coverage"] - single_metrics["average_coverage"]
        if cov_diff > 0:
            findings += f"- **Coverage**: Multi-agent system achieved {cov_diff:.1%} higher coverage "
            findings += f"({multi_metrics['average_coverage']:.3f} vs {single_metrics['average_coverage']:.3f}).\n"
        else:
            findings += f"- **Coverage**: Single agent achieved {abs(cov_diff):.1%} higher coverage "
            findings += f"({single_metrics['average_coverage']:.3f} vs {multi_metrics['average_coverage']:.3f}).\n"

        # Risks comparison
        risk_diff = multi_metrics["average_risks"] - single_metrics["average_risks"]
        if risk_diff > 0:
            findings += f"- **Risk Identification**: Multi-agent system identified {risk_diff:.1f} more risks on average "
            findings += f"({multi_metrics['average_risks']:.1f} vs {single_metrics['average_risks']:.1f}).\n"
        else:
            findings += f"- **Risk Identification**: Single agent identified {abs(risk_diff):.1f} more risks on average "
            findings += f"({single_metrics['average_risks']:.1f} vs {multi_metrics['average_risks']:.1f}).\n"

        # Recommendations comparison
        rec_diff = multi_metrics["average_recommendations"] - single_metrics["average_recommendations"]
        if rec_diff > 0:
            findings += f"- **Recommendations**: Multi-agent system provided {rec_diff:.1f} more recommendations on average "
            findings += f"({multi_metrics['average_recommendations']:.1f} vs {single_metrics['average_recommendations']:.1f}).\n"
        else:
            findings += f"- **Recommendations**: Single agent provided {abs(rec_diff):.1f} more recommendations on average "
            findings += f"({single_metrics['average_recommendations']:.1f} vs {multi_metrics['average_recommendations']:.1f}).\n"

        # Completeness comparison
        comp_diff = multi_metrics["average_completeness"] - single_metrics["average_completeness"]
        if comp_diff > 0:
            findings += f"- **Completeness**: Multi-agent system scored {comp_diff:.2f} points higher on completeness "
            findings += f"({multi_metrics['average_completeness']:.2f} vs {single_metrics['average_completeness']:.2f}).\n"
        else:
            findings += f"- **Completeness**: Single agent scored {abs(comp_diff):.2f} points higher on completeness "
            findings += f"({single_metrics['average_completeness']:.2f} vs {multi_metrics['average_completeness']:.2f}).\n"

        # Recommendation Quality comparison
        rec_quality_diff = multi_metrics["average_recommendation_quality"] - single_metrics["average_recommendation_quality"]
        if rec_quality_diff > 0:
            findings += f"- **Recommendation Quality**: Multi-agent system scored {rec_quality_diff:.2f} points higher "
            findings += f"({multi_metrics['average_recommendation_quality']:.2f} vs {single_metrics['average_recommendation_quality']:.2f}).\n"
        else:
            findings += f"- **Recommendation Quality**: Single agent scored {abs(rec_quality_diff):.2f} points higher "
            findings += f"({single_metrics['average_recommendation_quality']:.2f} vs {multi_metrics['average_recommendation_quality']:.2f}).\n"

        # Decision Support Quality comparison
        decision_quality_diff = multi_metrics["average_decision_support_quality"] - single_metrics["average_decision_support_quality"]
        if decision_quality_diff > 0:
            findings += f"- **Decision Support Quality**: Multi-agent system scored {decision_quality_diff:.2f} points higher "
            findings += f"({multi_metrics['average_decision_support_quality']:.2f} vs {single_metrics['average_decision_support_quality']:.2f}).\n"
        else:
            findings += f"- **Decision Support Quality**: Single agent scored {abs(decision_quality_diff):.2f} points higher "
            findings += f"({single_metrics['average_decision_support_quality']:.2f} vs {multi_metrics['average_decision_support_quality']:.2f}).\n"

        # Execution time comparison
        time_diff = multi_metrics["average_execution_time"] - single_metrics["average_execution_time"]
        if time_diff > 0:
            findings += f"- **Execution Time**: Multi-agent system took {time_diff:.2f}s longer on average "
            findings += f"({multi_metrics['average_execution_time']:.2f}s vs {single_metrics['average_execution_time']:.2f}s).\n"
        else:
            findings += f"- **Execution Time**: Single agent took {abs(time_diff):.2f}s longer on average "
            findings += f"({single_metrics['average_execution_time']:.2f}s vs {multi_metrics['average_execution_time']:.2f}s).\n"

        # Statistical significance
        if stat_df is not None:
            findings += "\n### Statistical Significance\n\n"
            if "coverage_p_value" in stat_df.columns:
                cov_p = stat_df["coverage_p_value"].iloc[0]
                if cov_p < 0.05:
                    findings += f"- Coverage difference is **statistically significant** (p={cov_p:.4f}).\n"
                else:
                    findings += f"- Coverage difference is **not statistically significant** (p={cov_p:.4f}).\n"

            if "completeness_p_value" in stat_df.columns:
                comp_p = stat_df["completeness_p_value"].iloc[0]
                if comp_p < 0.05:
                    findings += f"- Completeness difference is **statistically significant** (p={comp_p:.4f}).\n"
                else:
                    findings += f"- Completeness difference is **not statistically significant** (p={comp_p:.4f}).\n"

            if "recommendation_quality_p_value" in stat_df.columns:
                rec_q_p = stat_df["recommendation_quality_p_value"].iloc[0]
                if rec_q_p < 0.05:
                    findings += f"- Recommendation Quality difference is **statistically significant** (p={rec_q_p:.4f}).\n"
                else:
                    findings += f"- Recommendation Quality difference is **not statistically significant** (p={rec_q_p:.4f}).\n"

            if "decision_support_quality_p_value" in stat_df.columns:
                dec_q_p = stat_df["decision_support_quality_p_value"].iloc[0]
                if dec_q_p < 0.05:
                    findings += f"- Decision Support Quality difference is **statistically significant** (p={dec_q_p:.4f}).\n"
                else:
                    findings += f"- Decision Support Quality difference is **not statistically significant** (p={dec_q_p:.4f}).\n"

        findings += "\n### Conclusion\n\n"

        # Determine overall winner based on quality metrics (excluding execution time)
        multi_better_count = 0
        single_better_count = 0

        if multi_metrics["average_coverage"] > single_metrics["average_coverage"]:
            multi_better_count += 1
        else:
            single_better_count += 1

        if multi_metrics["average_risks"] > single_metrics["average_risks"]:
            multi_better_count += 1
        else:
            single_better_count += 1

        if multi_metrics["average_recommendations"] > single_metrics["average_recommendations"]:
            multi_better_count += 1
        else:
            single_better_count += 1

        if multi_metrics["average_completeness"] > single_metrics["average_completeness"]:
            multi_better_count += 1
        else:
            single_better_count += 1

        if multi_metrics["average_recommendation_quality"] > single_metrics["average_recommendation_quality"]:
            multi_better_count += 1
        else:
            single_better_count += 1

        if multi_metrics["average_decision_support_quality"] > single_metrics["average_decision_support_quality"]:
            multi_better_count += 1
        else:
            single_better_count += 1

        if multi_better_count > single_better_count:
            findings += "Based on the quality metrics above, the **specialized multi-agent system** outperformed the single-agent baseline "
            findings += f"in {multi_better_count} out of 6 quality metrics. "
            findings += "The new quality-focused metrics (Recommendation Quality and Decision Support Quality) provide deeper insight into the usefulness of outputs for decision-making. "
            findings += "The trade-off between quality and efficiency should be considered based on use case requirements.\n"
        elif single_better_count > multi_better_count:
            findings += "Based on the quality metrics above, the **single-agent system** outperformed the multi-agent system "
            findings += f"in {single_better_count} out of 6 quality metrics. "
            findings += "It also has faster execution times. "
            findings += "The new quality-focused metrics reveal that agent specialization did not provide clear benefits in terms of output quality and decision usefulness.\n"
        else:
            findings += "Based on the quality metrics above, both systems performed similarly across quality metrics. "
            findings += "The multi-agent system requires more execution time without clear quality benefits. "
            findings += "The new quality-focused metrics provide a more nuanced view of decision-support capabilities. "
            findings += "Further investigation may be needed to determine when agent specialization is beneficial.\n"

        return findings
