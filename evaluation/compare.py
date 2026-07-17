"""Compare evaluation results across retrieval backends."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from loguru import logger

from evaluation.metrics import EvaluationMetrics, RetrievalTestResult
from evaluation.report_generator import generate_comparison_markdown, load_json_results, write_markdown_report


def _metrics_from_payload(payload: dict) -> EvaluationMetrics:
	aggregate = payload["aggregate"]
	results = [
		RetrievalTestResult(
			original_query=result["original_query"],
			retrieval_query=result["retrieval_query"],
			retrieved_context_summary=result["retrieved_context_summary"],
			precision_at_5=result["precision_at_5"],
			precision_at_10=result["precision_at_10"],
			average_similarity=result["average_similarity"],
			retrieval_time_ms=result["retrieval_time_ms"],
			relevant_count=result["relevant_count"],
			retrieved_count=result["retrieved_count"],
			remarks=result["remarks"],
			hit_at_1=result.get("hit_at_1", False),
			hit_at_3=result.get("hit_at_3", False),
			hit_at_5=result.get("hit_at_5", False),
			raw_retrieval=result.get("raw_retrieval", {}),
		)
		for result in payload.get("results", [])
	]

	return EvaluationMetrics(
		backend=payload["backend"],
		num_retrieval_tests=aggregate["num_retrieval_tests"],
		average_precision_at_5=aggregate["average_precision_at_5"],
		average_precision_at_10=aggregate["average_precision_at_10"],
		average_similarity=aggregate["average_similarity"],
		average_retrieval_time_ms=aggregate["average_retrieval_time_ms"],
		total_nodes=aggregate["total_nodes"],
		total_relationships=aggregate["total_relationships"],
		relevance_threshold=aggregate["relevance_threshold"],
		embedding_provider=aggregate["embedding_provider"],
		average_hit_at_1=aggregate.get("average_hit_at_1", 0.0),
		average_hit_at_3=aggregate.get("average_hit_at_3", 0.0),
		average_hit_at_5=aggregate.get("average_hit_at_5", 0.0),
		similarity_distribution=aggregate.get("similarity_distribution", {}),
		results=results,
	)


def load_backend_results(result_paths: Iterable[Path | str]) -> dict[str, EvaluationMetrics]:
	"""Load one or more backend result files keyed by backend name."""
	loaded: dict[str, EvaluationMetrics] = {}
	for path in result_paths:
		payload = load_json_results(path)
		metrics = _metrics_from_payload(payload)
		loaded[metrics.backend] = metrics
		logger.info("Loaded backend results for {}", metrics.backend)
	return loaded


def compare_backends(
	result_paths: Iterable[Path | str],
	output_markdown_path: Path | str,
) -> Path:
	"""Generate a comparison markdown report from multiple backend JSON files."""
	results_by_backend = load_backend_results(result_paths)
	markdown = generate_comparison_markdown(results_by_backend)
	output_path = Path(output_markdown_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(markdown, encoding="utf-8")
	logger.info("Comparison report written to {}", output_path)
	return output_path
