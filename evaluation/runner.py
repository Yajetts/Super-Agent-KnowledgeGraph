"""Main runner for specialized agent evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from evaluation.dataset_loader import DatasetLoader
from evaluation.llm_judge import LLMJudge
from evaluation.metrics_aggregation import MetricsAggregator
from evaluation.metrics_multiagent import MetricsCalculator
from evaluation.multi_agent_runner import MultiAgentRunner
from evaluation.single_agent_runner import SingleAgentRunner
from evaluation.specialized_report_generator import SpecializedReportGenerator
from evaluation.visualization import Visualizer


class EvaluationRunner:
    """Orchestrate the complete evaluation pipeline."""

    def __init__(self, dataset_path: str | Path, results_dir: str | Path) -> None:
        self.dataset_path = Path(dataset_path)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.dataset_loader = DatasetLoader(self.dataset_path)
        self.single_agent_runner = SingleAgentRunner()
        self.multi_agent_runner = MultiAgentRunner()
        self.metrics_calculator = MetricsCalculator()
        self.llm_judge = LLMJudge()

    def run_single_agent_evaluation(self) -> None:
        """Run single agent baseline evaluation."""
        print("Running single agent evaluation...")
        tasks = self.dataset_loader.load_tasks()
        results = []

        for task in tasks:
            task_dict = {"task_id": task.task_id, "query": task.query}
            result = self.single_agent_runner.run(task_dict)
            
            # Calculate metrics
            response = result["response"]
            coverage = self.metrics_calculator.calculate_coverage(response)
            risk_count = self.metrics_calculator.count_risks(response)
            recommendation_count = self.metrics_calculator.count_recommendations(response)
            completeness = self.llm_judge.evaluate(task.query, response)
            
            # Calculate new quality metrics
            rec_quality = self.llm_judge.calculate_recommendation_quality(task.query, response)
            decision_quality = self.llm_judge.calculate_decision_support_quality(task.query, response)

            results.append({
                "task_id": result["task_id"],
                "query": result["query"],
                "response": result["response"],
                "execution_time": result["execution_time"],
                "coverage": coverage,
                "risk_count": risk_count,
                "recommendation_count": recommendation_count,
                "completeness_score": completeness,
                "recommendation_quality_score": rec_quality["overall_score"],
                "decision_support_quality_score": decision_quality["overall_score"],
            })

        df = pd.DataFrame(results)
        df.to_csv(self.results_dir / "single_agent_results.csv", index=False)
        print(f"Single agent evaluation complete. Results saved to {self.results_dir / 'single_agent_results.csv'}")

    def run_multi_agent_evaluation(self) -> None:
        """Run multi-agent system evaluation."""
        print("Running multi-agent evaluation...")
        tasks = self.dataset_loader.load_tasks()
        results = []

        for task in tasks:
            task_dict = {"task_id": task.task_id, "query": task.query}
            result = self.multi_agent_runner.run(task_dict)
            
            # Calculate metrics on final output
            final_output = result["final_output"]
            coverage = self.metrics_calculator.calculate_coverage(final_output)
            risk_count = self.metrics_calculator.count_risks(final_output)
            recommendation_count = self.metrics_calculator.count_recommendations(final_output)
            completeness = self.llm_judge.evaluate(task.query, final_output)
            
            # Calculate new quality metrics
            rec_quality = self.llm_judge.calculate_recommendation_quality(task.query, final_output)
            decision_quality = self.llm_judge.calculate_decision_support_quality(task.query, final_output)

            results.append({
                "task_id": result["task_id"],
                "query": result["query"],
                "research_output": result["research_output"],
                "risk_output": result["risk_output"],
                "strategy_output": result["strategy_output"],
                "final_output": result["final_output"],
                "execution_time": result["execution_time"],
                "coverage": coverage,
                "risk_count": risk_count,
                "recommendation_count": recommendation_count,
                "completeness_score": completeness,
                "recommendation_quality_score": rec_quality["overall_score"],
                "decision_support_quality_score": decision_quality["overall_score"],
            })

        df = pd.DataFrame(results)
        df.to_csv(self.results_dir / "multi_agent_results.csv", index=False)
        print(f"Multi-agent evaluation complete. Results saved to {self.results_dir / 'multi_agent_results.csv'}")

    def run_aggregation_and_analysis(self) -> None:
        """Aggregate metrics and run statistical tests."""
        print("Aggregating metrics and running statistical analysis...")
        aggregator = MetricsAggregator(self.results_dir)
        
        single_metrics = aggregator.aggregate_single_agent_metrics()
        multi_metrics = aggregator.aggregate_multi_agent_metrics()
        
        aggregator.save_aggregated_metrics(single_metrics, multi_metrics)
        
        statistical_results = aggregator.run_statistical_tests()
        print(f"Statistical analysis complete. Results saved to {self.results_dir / 'statistical_analysis.csv'}")

    def generate_visualizations(self) -> None:
        """Generate comparison charts."""
        print("Generating visualizations...")
        visualizer = Visualizer(self.results_dir)
        visualizer.generate_all_charts()
        print(f"Charts saved to {self.results_dir / 'charts'}")

    def generate_report(self) -> None:
        """Generate the final evaluation report."""
        print("Generating evaluation report...")
        report_generator = SpecializedReportGenerator(self.results_dir)
        report_path = self.results_dir.parent / "report.md"
        report_generator.generate_report(report_path)
        print(f"Report generated at {report_path}")

    def run_complete_evaluation(self) -> None:
        """Run the complete evaluation pipeline."""
        self.run_single_agent_evaluation()
        self.run_multi_agent_evaluation()
        self.run_aggregation_and_analysis()
        self.generate_visualizations()
        self.generate_report()
        print("\nEvaluation complete!")


if __name__ == "__main__":
    runner = EvaluationRunner(
        dataset_path="evaluation/tasks.csv",
        results_dir="evaluation/results",
    )
    runner.run_complete_evaluation()
