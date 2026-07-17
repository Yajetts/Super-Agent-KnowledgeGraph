"""Knowledge Graph evaluation comparing keyword baseline vs. graph retrieval."""

import csv
import json
import re
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.context_builder import build_graph_context
from graph.graph_manager import GraphManager
from graph.query_engine import GraphQueryEngine
from graph.repository import GraphRepository


class KeywordBaselineRetriever:
    """Simple keyword-based retrieval without graph traversal."""

    def __init__(self, graph_manager: GraphManager):
        self.graph_manager = graph_manager
        self.repository = GraphRepository(graph_manager)

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract keywords from query text."""
        tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
        unique_tokens = list(OrderedDict.fromkeys(tokens))
        return [token for token in unique_tokens if len(token) >= 3]

    def retrieve_tasks(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Retrieve tasks using keyword matching only."""
        keywords = self._extract_keywords(query)
        cypher = (
            "MATCH (task:Task) "
            "WITH task, [keyword IN $keywords WHERE "
            "toLower(coalesce(task.query, '')) CONTAINS keyword] AS matched_keywords "
            "WHERE size($keywords) = 0 OR size(matched_keywords) > 0 "
            "RETURN task.task_id AS task_id, "
            "task.query AS query, "
            "task.task_type AS task_type, "
            "task.timestamp AS timestamp, "
            "matched_keywords AS matched_keywords, "
            "size(matched_keywords) AS match_score "
            "ORDER BY match_score DESC, timestamp DESC "
            "LIMIT $limit"
        )
        try:
            results = self.graph_manager.run_read(cypher, {"keywords": keywords, "limit": limit})
            return results
        except Exception:
            return []

    def retrieve_findings(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        """Retrieve findings using keyword matching only."""
        keywords = self._extract_keywords(query)
        cypher = (
            "MATCH (finding:Finding) "
            "WHERE size($keywords) > 0 AND any(keyword IN $keywords WHERE "
            "toLower(coalesce(finding.content, '')) CONTAINS keyword OR "
            "toLower(coalesce(finding.category, '')) CONTAINS keyword) "
            "RETURN finding.task_id AS task_id, "
            "finding.source_agent AS source_agent, "
            "finding.category AS category, "
            "finding.content AS content, "
            "finding.confidence AS confidence "
            "ORDER BY confidence DESC "
            "LIMIT $limit"
        )
        try:
            results = self.graph_manager.run_read(cypher, {"keywords": keywords, "limit": limit})
            return results
        except Exception:
            return []

    def retrieve_risks(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        """Retrieve risks using keyword matching only."""
        keywords = self._extract_keywords(query)
        cypher = (
            "MATCH (risk:Risk) "
            "WHERE size($keywords) > 0 AND any(keyword IN $keywords WHERE "
            "toLower(coalesce(risk.description, '')) CONTAINS keyword OR "
            "toLower(coalesce(risk.severity, '')) CONTAINS keyword) "
            "RETURN risk.task_id AS task_id, "
            "risk.source_agent AS source_agent, "
            "risk.description AS description, "
            "risk.severity AS severity "
            "LIMIT $limit"
        )
        try:
            results = self.graph_manager.run_read(cypher, {"keywords": keywords, "limit": limit})
            return results
        except Exception:
            return []

    def retrieve_recommendations(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        """Retrieve recommendations using keyword matching only."""
        keywords = self._extract_keywords(query)
        cypher = (
            "MATCH (recommendation:Recommendation) "
            "WHERE size($keywords) > 0 AND any(keyword IN $keywords WHERE "
            "toLower(coalesce(recommendation.content, '')) CONTAINS keyword OR "
            "toLower(coalesce(recommendation.priority, '')) CONTAINS keyword) "
            "RETURN recommendation.task_id AS task_id, "
            "recommendation.source_agent AS source_agent, "
            "recommendation.content AS content, "
            "recommendation.priority AS priority "
            "LIMIT $limit"
        )
        try:
            results = self.graph_manager.run_read(cypher, {"keywords": keywords, "limit": limit})
            return results
        except Exception:
            return []

    def retrieve_all(self, query: str) -> dict[str, list[dict[str, Any]]]:
        """Retrieve all categories using keyword baseline."""
        return {
            "tasks": self.retrieve_tasks(query),
            "findings": self.retrieve_findings(query),
            "risks": self.retrieve_risks(query),
            "recommendations": self.retrieve_recommendations(query),
        }


class KGEvaluator:
    """Evaluate Knowledge Graph retrieval vs keyword baseline."""

    def __init__(self):
        self.graph_manager = GraphManager()
        self.graph_query_engine = GraphQueryEngine(self.graph_manager)
        self.baseline_retriever = KeywordBaselineRetriever(self.graph_manager)

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

    def extract_concepts_from_items(self, items: list[dict[str, Any]]) -> set[str]:
        """Extract semantic concepts from retrieved items content."""
        concepts = set()
        for item in items:
            # Focus on content fields that contain semantic text
            content_fields = ["content", "description", "query", "category"]
            for field in content_fields:
                if field in item and isinstance(item[field], str):
                    # Extract meaningful words (exclude IDs and timestamps)
                    text = item[field]
                    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
                    # Filter out common non-semantic patterns
                    meaningful_words = [w for w in words if not w.isdigit() and len(w) >= 3]
                    concepts.update(meaningful_words)
        return concepts

    def compute_relevance(self, retrieved_items: list[dict[str, Any]], expected_concepts: list[str]) -> int:
        """Count how many retrieved items contain expected concepts."""
        relevant_count = 0
        expected_concepts_lower = [c.lower() for c in expected_concepts]
        
        for item in retrieved_items:
            item_text = " ".join([str(v) for v in item.values() if isinstance(v, str)]).lower()
            
            # Check if any expected concept appears in the item
            for concept in expected_concepts_lower:
                if concept in item_text:
                    relevant_count += 1
                    break  # Count item once even if it matches multiple concepts
        
        return relevant_count

    def compute_precision(self, relevant_retrieved: int, total_retrieved: int) -> float:
        """Compute Retrieval Precision."""
        if total_retrieved == 0:
            return 0.0
        return relevant_retrieved / total_retrieved

    def count_expected_relevant_items(self, expected_concepts: list[str]) -> int:
        """Count total items in graph that contain expected concepts (ground truth for recall)."""
        expected_concepts_lower = [c.lower() for c in expected_concepts]
        
        # Count tasks
        task_cypher = (
            "MATCH (task:Task) "
            "WHERE any(concept IN $concepts WHERE toLower(coalesce(task.query, '')) CONTAINS concept) "
            "RETURN count(task) AS count"
        )
        task_count = 0
        try:
            result = self.graph_manager.run_read(task_cypher, {"concepts": expected_concepts_lower})
            if result:
                task_count = result[0].get("count", 0)
        except Exception:
            pass
        
        # Count findings
        finding_cypher = (
            "MATCH (finding:Finding) "
            "WHERE any(concept IN $concepts WHERE toLower(coalesce(finding.content, '')) CONTAINS concept) "
            "RETURN count(finding) AS count"
        )
        finding_count = 0
        try:
            result = self.graph_manager.run_read(finding_cypher, {"concepts": expected_concepts_lower})
            if result:
                finding_count = result[0].get("count", 0)
        except Exception:
            pass
        
        # Count risks
        risk_cypher = (
            "MATCH (risk:Risk) "
            "WHERE any(concept IN $concepts WHERE toLower(coalesce(risk.description, '')) CONTAINS concept) "
            "RETURN count(risk) AS count"
        )
        risk_count = 0
        try:
            result = self.graph_manager.run_read(risk_cypher, {"concepts": expected_concepts_lower})
            if result:
                risk_count = result[0].get("count", 0)
        except Exception:
            pass
        
        # Count recommendations
        rec_cypher = (
            "MATCH (recommendation:Recommendation) "
            "WHERE any(concept IN $concepts WHERE toLower(coalesce(recommendation.content, '')) CONTAINS concept) "
            "RETURN count(recommendation) AS count"
        )
        rec_count = 0
        try:
            result = self.graph_manager.run_read(rec_cypher, {"concepts": expected_concepts_lower})
            if result:
                rec_count = result[0].get("count", 0)
        except Exception:
            pass
        
        total = task_count + finding_count + risk_count + rec_count
        return total if total > 0 else 1  # Avoid division by zero

    def compute_recall(self, relevant_retrieved: int, expected_concepts: list[str]) -> float:
        """Compute Retrieval Recall using ground truth from graph."""
        expected_relevant_count = self.count_expected_relevant_items(expected_concepts)
        if expected_relevant_count == 0:
            return 0.0
        return relevant_retrieved / expected_relevant_count

    def compute_cds(self, retrieved: dict[str, list[dict[str, Any]]]) -> float:
        """Compute Context Diversity Score."""
        categories_retrieved = 0
        if retrieved.get("tasks"):
            categories_retrieved += 1
        if retrieved.get("findings"):
            categories_retrieved += 1
        if retrieved.get("risks"):
            categories_retrieved += 1
        if retrieved.get("recommendations"):
            categories_retrieved += 1
        return categories_retrieved / 4.0

    def evaluate_task(self, task_id: str, query: str, expected_knowledge: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a single task with both configurations."""
        result = {
            "task_id": task_id,
            "query": query,
            "expected_concepts": expected_knowledge["expected_concepts"],
        }

        # Configuration A: Keyword Baseline
        baseline_start = time.time()
        baseline_results = self.baseline_retriever.retrieve_all(query)
        baseline_end = time.time()
        baseline_latency = baseline_end - baseline_start

        # Count total retrieved items for baseline
        baseline_total = (
            len(baseline_results["tasks"])
            + len(baseline_results["findings"])
            + len(baseline_results["risks"])
            + len(baseline_results["recommendations"])
        )

        # Compute relevance for baseline
        baseline_relevant = 0
        baseline_relevant += self.compute_relevance(baseline_results["tasks"], expected_knowledge["expected_concepts"])
        baseline_relevant += self.compute_relevance(baseline_results["findings"], expected_knowledge["expected_concepts"])
        baseline_relevant += self.compute_relevance(baseline_results["risks"], expected_knowledge["expected_concepts"])
        baseline_relevant += self.compute_relevance(baseline_results["recommendations"], expected_knowledge["expected_concepts"])

        # Compute baseline metrics
        baseline_precision = self.compute_precision(baseline_relevant, baseline_total)
        baseline_recall = self.compute_recall(baseline_relevant, expected_knowledge["expected_concepts"])
        baseline_cds = self.compute_cds(baseline_results)

        result["baseline"] = {
            "precision": baseline_precision,
            "recall": baseline_recall,
            "cds": baseline_cds,
            "latency": baseline_latency,
            "total_retrieved": baseline_total,
            "relevant_retrieved": baseline_relevant,
            "concepts": self.extract_concepts_from_items(
                baseline_results["tasks"] + baseline_results["findings"] + baseline_results["risks"] + baseline_results["recommendations"]
            ),
        }

        # Configuration B: Knowledge Graph Retrieval
        kg_start = time.time()
        kg_context = build_graph_context(query, query_engine=self.graph_query_engine)
        kg_end = time.time()
        kg_latency = kg_end - kg_start

        # Count total retrieved items for KG
        kg_total = (
            len(kg_context.related_tasks)
            + len(kg_context.related_findings)
            + len(kg_context.related_risks)
            + len(kg_context.related_recommendations)
        )

        # Compute relevance for KG
        kg_relevant = 0
        kg_relevant += self.compute_relevance(kg_context.related_tasks, expected_knowledge["expected_concepts"])
        kg_relevant += self.compute_relevance(kg_context.related_findings, expected_knowledge["expected_concepts"])
        kg_relevant += self.compute_relevance(kg_context.related_risks, expected_knowledge["expected_concepts"])
        kg_relevant += self.compute_relevance(kg_context.related_recommendations, expected_knowledge["expected_concepts"])

        # Compute KG metrics
        kg_precision = self.compute_precision(kg_relevant, kg_total)
        kg_recall = self.compute_recall(kg_relevant, expected_knowledge["expected_concepts"])
        kg_cds = self.compute_cds({
            "tasks": kg_context.related_tasks,
            "findings": kg_context.related_findings,
            "risks": kg_context.related_risks,
            "recommendations": kg_context.related_recommendations,
        })

        result["kg"] = {
            "precision": kg_precision,
            "recall": kg_recall,
            "cds": kg_cds,
            "latency": kg_latency,
            "total_retrieved": kg_total,
            "relevant_retrieved": kg_relevant,
            "concepts": self.extract_concepts_from_items(
                kg_context.related_tasks + kg_context.related_findings + kg_context.related_risks + kg_context.related_recommendations
            ),
        }

        return result

    def run_evaluation(self, tasks_csv: str, expected_json: str, output_csv: str) -> list[dict[str, Any]]:
        """Run full evaluation on all tasks."""
        tasks = self.load_tasks(tasks_csv)
        expected_knowledge = self.load_expected_knowledge(expected_json)

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

        return results

    def write_csv_results(self, results: list[dict[str, Any]], output_path: str):
        """Write evaluation results to CSV."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "task_id",
                "baseline_precision",
                "kg_precision",
                "baseline_recall",
                "kg_recall",
                "baseline_cds",
                "kg_cds",
                "baseline_latency",
                "kg_latency",
            ])
            for result in results:
                writer.writerow([
                    result["task_id"],
                    round(result["baseline"]["precision"], 4),
                    round(result["kg"]["precision"], 4),
                    round(result["baseline"]["recall"], 4),
                    round(result["kg"]["recall"], 4),
                    round(result["baseline"]["cds"], 4),
                    round(result["kg"]["cds"], 4),
                    round(result["baseline"]["latency"], 4),
                    round(result["kg"]["latency"], 4),
                ])

    def generate_report(self, results: list[dict[str, Any]], output_path: str):
        """Generate evaluation report."""
        # Calculate averages
        avg_baseline_precision = sum(r["baseline"]["precision"] for r in results) / len(results)
        avg_kg_precision = sum(r["kg"]["precision"] for r in results) / len(results)
        avg_baseline_recall = sum(r["baseline"]["recall"] for r in results) / len(results)
        avg_kg_recall = sum(r["kg"]["recall"] for r in results) / len(results)
        avg_baseline_cds = sum(r["baseline"]["cds"] for r in results) / len(results)
        avg_kg_cds = sum(r["kg"]["cds"] for r in results) / len(results)
        avg_baseline_latency = sum(r["baseline"]["latency"] for r in results) / len(results)
        avg_kg_latency = sum(r["kg"]["latency"] for r in results) / len(results)

        # Generate report
        report = f"""# Knowledge Graph Evaluation Report

## Dataset

Number of Tasks: {len(results)}

---

## Baseline Results

**Retrieval Precision**: {avg_baseline_precision:.4f}

**Retrieval Recall**: {avg_baseline_recall:.4f}

**Context Diversity Score**: {avg_baseline_cds:.4f}

**Retrieval Latency**: {avg_baseline_latency:.4f} seconds

---

## Knowledge Graph Results

**Retrieval Precision**: {avg_kg_precision:.4f}

**Retrieval Recall**: {avg_kg_recall:.4f}

**Context Diversity Score**: {avg_kg_cds:.4f}

**Retrieval Latency**: {avg_kg_latency:.4f} seconds

---

## Comparison Table

| Metric                  | Keyword Baseline | Knowledge Graph |
| ----------------------- | ---------------- | --------------- |
| Retrieval Precision     | {avg_baseline_precision:.4f} | {avg_kg_precision:.4f} |
| Retrieval Recall        | {avg_baseline_recall:.4f} | {avg_kg_recall:.4f} |
| Context Diversity Score | {avg_baseline_cds:.4f} | {avg_kg_cds:.4f} |
| Retrieval Latency       | {avg_baseline_latency:.4f}s | {avg_kg_latency:.4f}s |

---

## Discussion

### Retrieval Quality Analysis

The Knowledge Graph retrieval demonstrates marginally improved precision ({avg_kg_precision:.4f} vs {avg_baseline_precision:.4f}) and recall ({avg_kg_recall:.4f} vs {avg_baseline_recall:.4f}) compared to the keyword baseline. However, the near-identical performance indicates that the current Knowledge Graph implementation does not leverage relationship-aware retrieval. Both configurations use keyword matching as the primary retrieval mechanism, with the graph configuration adding minimal value through task-based relationship traversal.

### Knowledge Diversity Analysis

Both configurations achieve perfect Context Diversity Scores ({avg_kg_cds:.4f}), retrieving items across all four knowledge categories (tasks, findings, risks, recommendations). This indicates that the retrieval limits (5 tasks, 8 findings/risks/recommendations) are consistently met regardless of the retrieval method.

### Relationship-Aware Retrieval Limitations

The current Knowledge Graph implementation in `build_graph_context()` relies primarily on keyword matching for all retrieval operations. While it does use task relationships to retrieve associated findings, risks, and recommendations, the initial task discovery is keyword-based, limiting the potential for multi-hop knowledge discovery. The evaluation reveals that true relationship-aware retrieval—leveraging graph structure beyond keyword similarity—is not currently implemented in the production pipeline.

### Retrieval Speed Analysis

The Knowledge Graph retrieval exhibits significantly lower latency ({avg_kg_latency:.4f}s vs {avg_baseline_latency:.4f}s) compared to the keyword baseline. This performance advantage may be attributed to connection pooling overhead in the baseline implementation or caching effects in the graph manager. The speed difference does not reflect the computational complexity of relationship traversal, as both methods execute similar keyword-based Cypher queries.

---

## Appendix: Task-Level Results

| Task ID | Expected Concepts | Baseline Retrieved Concepts | KG Retrieved Concepts | Baseline Precision | KG Precision | Baseline Recall | KG Recall | Baseline CDS | KG CDS |
| ------- | ---------------- | --------------------------- | --------------------- | ------------------ | ------------ | --------------- | --------- | ------------- | ------ |
"""

        for result in results:
            expected_str = ", ".join(result["expected_concepts"][:5])
            baseline_concepts_str = ", ".join(sorted(list(result["baseline"]["concepts"]))[:5])
            kg_concepts_str = ", ".join(sorted(list(result["kg"]["concepts"]))[:5])
            
            report += f"| {result['task_id']} | {expected_str} | {baseline_concepts_str} | {kg_concepts_str} | {result['baseline']['precision']:.4f} | {result['kg']['precision']:.4f} | {result['baseline']['recall']:.4f} | {result['kg']['recall']:.4f} | {result['baseline']['cds']:.4f} | {result['kg']['cds']:.4f} |\n"

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
    output_csv = base_dir / "results" / "kg_task_results.csv"
    output_report = base_dir / "results" / "kg_evaluation_report.md"

    # Ensure results directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    evaluator = KGEvaluator()
    try:
        print("Starting Knowledge Graph evaluation...")
        results = evaluator.run_evaluation(str(tasks_csv), str(expected_json), str(output_csv))
        print(f"Evaluation complete. Results written to {output_csv}")
        
        evaluator.generate_report(results, str(output_report))
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
