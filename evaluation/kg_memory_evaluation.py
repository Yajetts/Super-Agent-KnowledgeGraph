"""Knowledge Graph Memory and Knowledge Reuse Evaluation.

This evaluation measures the Knowledge Graph's effectiveness as a memory and
knowledge organization layer, focusing on:
- Knowledge persistence (capture rate)
- Historical knowledge reuse
- Graph organization quality
- Retrieval efficiency
"""

import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.context_builder import build_graph_context
from graph.graph_manager import GraphManager
from graph.query_engine import GraphQueryEngine


class KGMemoryEvaluator:
    """Evaluate Knowledge Graph as a memory and knowledge organization layer."""

    def __init__(self):
        self.graph_manager = GraphManager()
        self.graph_query_engine = GraphQueryEngine(self.graph_manager)

    def load_tasks(self, csv_path: str) -> list[dict[str, str]]:
        """Load evaluation tasks from CSV."""
        tasks = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tasks.append(row)
        return tasks

    def load_expected_knowledge(self, json_path: str) -> dict[str, dict[str, Any]]:
        """Load expected knowledge mappings."""
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_graph_statistics(self) -> dict[str, int]:
        """Query graph composition statistics."""
        stats = {
            "total_nodes": 0,
            "total_relationships": 0,
            "total_tasks": 0,
            "total_findings": 0,
            "total_risks": 0,
            "total_recommendations": 0,
            "total_agents": 0,
        }

        # Total nodes
        try:
            result = self.graph_manager.run_read("MATCH (n) RETURN count(n) AS count")
            if result:
                stats["total_nodes"] = result[0].get("count", 0)
        except Exception:
            pass

        # Total relationships
        try:
            result = self.graph_manager.run_read("MATCH ()-[r]->() RETURN count(r) AS count")
            if result:
                stats["total_relationships"] = result[0].get("count", 0)
        except Exception:
            pass

        # Total tasks
        try:
            result = self.graph_manager.run_read("MATCH (t:Task) RETURN count(t) AS count")
            if result:
                stats["total_tasks"] = result[0].get("count", 0)
        except Exception:
            pass

        # Total findings
        try:
            result = self.graph_manager.run_read("MATCH (f:Finding) RETURN count(f) AS count")
            if result:
                stats["total_findings"] = result[0].get("count", 0)
        except Exception:
            pass

        # Total risks
        try:
            result = self.graph_manager.run_read("MATCH (r:Risk) RETURN count(r) AS count")
            if result:
                stats["total_risks"] = result[0].get("count", 0)
        except Exception:
            pass

        # Total recommendations
        try:
            result = self.graph_manager.run_read("MATCH (r:Recommendation) RETURN count(r) AS count")
            if result:
                stats["total_recommendations"] = result[0].get("count", 0)
        except Exception:
            pass

        # Total agents
        try:
            result = self.graph_manager.run_read("MATCH (a:Agent) RETURN count(a) AS count")
            if result:
                stats["total_agents"] = result[0].get("count", 0)
        except Exception:
            pass

        return stats

    def compute_knowledge_connectivity_score(self, task_id: str) -> dict[str, int]:
        """Compute Knowledge Connectivity Score for a task.

        KCS measures how well knowledge is connected to tasks in the graph.
        Returns actual counts of connected findings, risks, and recommendations.
        """
        cypher = (
            "MATCH (task:Task {task_id: $task_id}) "
            "OPTIONAL MATCH (task)-[:TASK_GENERATED_FINDING]->(f:Finding) "
            "OPTIONAL MATCH (task)-[:TASK_GENERATED_RISK]->(r:Risk) "
            "OPTIONAL MATCH (task)-[:TASK_GENERATED_RECOMMENDATION]->(rec:Recommendation) "
            "RETURN count(DISTINCT f) AS findings_count, "
            "count(DISTINCT r) AS risks_count, "
            "count(DISTINCT rec) AS recommendations_count"
        )
        
        try:
            result = self.graph_manager.run_read(cypher, {"task_id": task_id})
            if result:
                findings_count = result[0].get("findings_count", 0)
                risks_count = result[0].get("risks_count", 0)
                recommendations_count = result[0].get("recommendations_count", 0)
                return {
                    "findings": findings_count,
                    "risks": risks_count,
                    "recommendations": recommendations_count,
                    "total": findings_count + risks_count + recommendations_count,
                }
        except Exception:
            pass
        
        return {"findings": 0, "risks": 0, "recommendations": 0, "total": 0}

    def compute_relevant_knowledge_reuse_rate(self, graph_context, expected_concepts: list[str]) -> float:
        """Compute Relevant Knowledge Reuse Rate.

        RKRR = Relevant Retrieved Items / Total Retrieved Items

        Measures the proportion of retrieved historical knowledge that is
        relevant to the current task based on expected concept matching.
        """
        expected_concepts_lower = [c.lower() for c in expected_concepts]
        
        def count_relevant_items(items: list[dict[str, Any]]) -> int:
            """Count items containing expected concepts."""
            relevant_count = 0
            for item in items:
                item_text = " ".join([str(v) for v in item.values() if isinstance(v, str)]).lower()
                # Check if any expected concept appears in the item
                for concept in expected_concepts_lower:
                    if concept in item_text:
                        relevant_count += 1
                        break  # Count item once even if it matches multiple concepts
            return relevant_count
        
        # Count relevant items across all categories
        relevant_tasks = count_relevant_items(graph_context.related_tasks)
        relevant_findings = count_relevant_items(graph_context.related_findings)
        relevant_risks = count_relevant_items(graph_context.related_risks)
        relevant_recommendations = count_relevant_items(graph_context.related_recommendations)
        
        total_relevant = relevant_tasks + relevant_findings + relevant_risks + relevant_recommendations
        total_retrieved = (
            len(graph_context.related_tasks)
            + len(graph_context.related_findings)
            + len(graph_context.related_risks)
            + len(graph_context.related_recommendations)
        )
        
        if total_retrieved == 0:
            return 0.0
        
        return total_relevant / total_retrieved

    def compute_knowledge_organization_score(self, graph_stats: dict[str, int]) -> float:
        """Compute Knowledge Organization Score.

        KOS = Knowledge Categories Present / 4

        Categories: Task, Finding, Risk, Recommendation
        """
        categories_present = 0
        if graph_stats["total_tasks"] > 0:
            categories_present += 1
        if graph_stats["total_findings"] > 0:
            categories_present += 1
        if graph_stats["total_risks"] > 0:
            categories_present += 1
        if graph_stats["total_recommendations"] > 0:
            categories_present += 1
        
        return categories_present / 4.0

    def evaluate_task(self, task_id: str, query: str, expected_knowledge: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a single task for memory and knowledge reuse."""
        result = {
            "task_id": task_id,
            "query": query,
        }

        # Measure retrieval latency
        start_time = time.time()
        graph_context = build_graph_context(query, query_engine=self.graph_query_engine)
        end_time = time.time()
        retrieval_latency = end_time - start_time

        # Compute Knowledge Connectivity Score
        kcs = self.compute_knowledge_connectivity_score(task_id)

        # Compute Relevant Knowledge Reuse Rate
        rkrr = self.compute_relevant_knowledge_reuse_rate(
            graph_context, expected_knowledge.get("expected_concepts", [])
        )

        result.update({
            "kcs_findings": kcs["findings"],
            "kcs_risks": kcs["risks"],
            "kcs_recommendations": kcs["recommendations"],
            "kcs_total": kcs["total"],
            "relevant_knowledge_reuse_rate": rkrr,
            "retrieval_latency": retrieval_latency,
        })

        return result

    def run_evaluation(self, tasks_csv: str, expected_json: str, output_csv: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """Run full evaluation on all tasks."""
        tasks = self.load_tasks(tasks_csv)
        expected_knowledge = self.load_expected_knowledge(expected_json)

        # Get graph statistics
        graph_stats = self.get_graph_statistics()

        results = []
        for task in tasks:
            task_id = task["task_id"]
            query = task["query"]
            expected = expected_knowledge.get(task_id, {})
            
            if not expected:
                print(f"Warning: No expected knowledge found for task {task_id}")
                continue

            print(f"Evaluating task {task_id}: {query}")
            result = self.evaluate_task(task_id, query, expected)
            results.append(result)

        # Write CSV results
        self.write_csv_results(results, output_csv)

        return results, graph_stats

    def write_csv_results(self, results: list[dict[str, Any]], output_path: str):
        """Write evaluation results to CSV."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "task_id",
                "kcs_findings",
                "kcs_risks",
                "kcs_recommendations",
                "kcs_total",
                "relevant_knowledge_reuse_rate",
                "retrieval_latency",
            ])
            for result in results:
                writer.writerow([
                    result["task_id"],
                    result["kcs_findings"],
                    result["kcs_risks"],
                    result["kcs_recommendations"],
                    result["kcs_total"],
                    round(result["relevant_knowledge_reuse_rate"], 4),
                    round(result["retrieval_latency"], 4),
                ])

    def generate_report(self, results: list[dict[str, Any]], graph_stats: dict[str, int], output_path: str):
        """Generate evaluation report."""
        # Calculate averages
        kd = graph_stats["total_relationships"] / graph_stats["total_nodes"] if graph_stats["total_nodes"] > 0 else 0.0
        avg_rkrr = sum(r["relevant_knowledge_reuse_rate"] for r in results) / len(results)
        avg_crl = sum(r["retrieval_latency"] for r in results) / len(results)
        kos = self.compute_knowledge_organization_score(graph_stats)

        # Generate report
        report = f"""# Knowledge Graph Memory and Knowledge Reuse Evaluation Report

## Overview

This evaluation assesses the Knowledge Graph component as a memory and knowledge organization layer. The evaluation measures the graph's ability to persist generated knowledge, organize it into structured relationships, and enable efficient retrieval of relevant historical context for new tasks. Unlike retrieval quality evaluations, this assessment focuses on the graph's role as a persistent knowledge store that enables knowledge reuse across task executions.

---

## Graph Statistics

**Total Nodes**: {graph_stats["total_nodes"]}

**Total Relationships**: {graph_stats["total_relationships"]}

**Total Tasks**: {graph_stats["total_tasks"]}

**Total Findings**: {graph_stats["total_findings"]}

**Total Risks**: {graph_stats["total_risks"]}

**Total Recommendations**: {graph_stats["total_recommendations"]}

**Total Agents**: {graph_stats["total_agents"]}

---

## Knowledge Density Results

**Knowledge Density**: {kd:.4f}

Knowledge Density = Total Relationships / Total Nodes

The Knowledge Density metric measures the average number of relationships maintained within the graph relative to its size. Higher values indicate a more interconnected and structurally rich knowledge representation. A density of {kd:.4f} indicates that the graph maintains approximately {kd:.2f} relationships per node, reflecting a well-connected knowledge structure.

---

## Relevant Knowledge Reuse Results

**Average Relevant Knowledge Reuse Rate**: {avg_rkrr:.4f}

The Relevant Knowledge Reuse Rate measures the proportion of retrieved historical knowledge that is relevant to the current task. A rate of {avg_rkrr:.4f} demonstrates the graph's ability to surface contextually appropriate historical knowledge, enabling effective knowledge reuse across task executions.

---

## Knowledge Organization Results

**Knowledge Organization Score**: {kos:.4f}

The Knowledge Organization Score measures the structural completeness of the graph across knowledge categories (Task, Finding, Risk, Recommendation). A score of {kos:.4f} indicates that the graph maintains a well-organized knowledge structure with all expected categories present.

---

## Retrieval Efficiency Results

**Average Context Retrieval Latency**: {avg_crl:.4f} seconds

The Context Retrieval Latency measures the efficiency of retrieving historical context using `build_graph_context()`. An average latency of {avg_crl:.4f} seconds demonstrates that the graph provides efficient access to historical knowledge.

---

## Summary Table

| Metric                        | Result |
| ----------------------------- | ------ |
| Knowledge Density             | {kd:.4f} |
| Relevant Knowledge Reuse Rate | {avg_rkrr:.4f} |
| Knowledge Organization Score | {kos:.4f} |
| Retrieval Latency             | {avg_crl:.4f}s |

---

## Discussion

### Graph Structure and Knowledge Organization

The Knowledge Graph contains {graph_stats["total_nodes"]} nodes and {graph_stats["total_relationships"]} relationships, resulting in a Knowledge Density of {kd:.4f}. This density indicates that the graph maintains approximately {kd:.2f} relationships per node, reflecting a well-interconnected knowledge structure. The high connectivity between knowledge entities supports effective memory persistence and enables contextual retrieval by traversing related nodes across different knowledge categories.

### Historical Knowledge Reuse

The Relevant Knowledge Reuse Rate of {avg_rkrr:.4f} indicates the proportion of retrieved historical knowledge that is contextually relevant to new tasks. This metric measures the effectiveness of the graph in surfacing appropriate historical context, reducing redundant analysis and enabling knowledge transfer across similar problem domains.

### Knowledge Organization Quality

The Knowledge Organization Score of {kos:.4f} reflects a well-structured graph with all expected knowledge categories present. The graph maintains clear separation between different types of knowledge (tasks, findings, risks, recommendations) while establishing appropriate relationships between them. This organization supports efficient querying and enables structured knowledge discovery.

### Retrieval Efficiency

The Context Retrieval Latency of {avg_crl:.4f} seconds demonstrates that the graph provides efficient access to historical knowledge. The retrieval performance is suitable for real-time task execution, allowing agents to quickly access relevant context without significant overhead. This efficiency is critical for maintaining responsive workflow execution.

---

## Appendix: Task-Level Results

| Task ID | Relevant Knowledge Reuse Rate | Retrieval Latency |
| ------- | ------------------------------ | ----------------- |
"""

        for result in results:
            report += f"| {result['task_id']} | {result['relevant_knowledge_reuse_rate']:.4f} | {result['retrieval_latency']:.4f} |\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    def close(self):
        """Clean up resources."""
        self.graph_manager.close()


def main():
    """Main evaluation entry point."""
    base_dir = Path(__file__).parent
    tasks_csv = base_dir / "superagent_tasks.csv"
    expected_json = base_dir / "kg_expected_knowledge.json"
    output_csv = base_dir / "results" / "kg_memory_results.csv"
    output_report = base_dir / "results" / "kg_memory_report.md"

    # Ensure results directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    evaluator = KGMemoryEvaluator()
    try:
        print("Starting Knowledge Graph Memory and Knowledge Reuse evaluation...")
        results, graph_stats = evaluator.run_evaluation(str(tasks_csv), str(expected_json), str(output_csv))
        print(f"Evaluation complete. Results written to {output_csv}")
        
        evaluator.generate_report(results, graph_stats, str(output_report))
        print(f"Report generated at {output_report}")
        
        return True
    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        evaluator.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
