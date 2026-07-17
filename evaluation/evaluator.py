"""Retrieval evaluation orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from evaluation.backends.base import RetrievalBackend
from evaluation.dataset import EvaluationRecord, load_evaluation_dataset
from evaluation.metrics import (
	EvaluationMetrics,
	RetrievalTestResult,
	aggregate_similarity_distribution,
	average_hit_rate,
	evaluate_retrieval_result,
)
from evaluation.report_generator import write_json_results, write_markdown_report
from evaluation.similarity import SimilarityScorer, create_embedding_provider


@dataclass(frozen=True)
class EvaluatorConfig:
	"""Configuration for a retrieval evaluation run."""

	dataset_path: Path
	results_dir: Path
	markdown_report_path: Path
	relevance_threshold: float = 0.75
	use_percentile_relevance: bool = True
	relevance_percentile: float = 50.0
	prefer_openai_embeddings: bool = True


class RetrievalEvaluator:
	"""Run retrieval evaluation for one backend against the baseline dataset."""

	def __init__(
		self,
		backend: RetrievalBackend,
		config: EvaluatorConfig,
		scorer: SimilarityScorer | None = None,
	) -> None:
		self.backend = backend
		self.config = config
		self.scorer = scorer or SimilarityScorer(
			provider=create_embedding_provider(prefer_openai=config.prefer_openai_embeddings),
			relevance_threshold=config.relevance_threshold,
			use_percentile_relevance=config.use_percentile_relevance,
			relevance_percentile=config.relevance_percentile,
		)

	@property
	def embedding_provider_name(self) -> str:
		provider = self.scorer.provider
		return provider.__class__.__name__

	def _fetch_graph_counts(self) -> tuple[int, int]:
		graph_manager = getattr(self.backend, "_graph_manager", None)
		if graph_manager is None:
			return 0, 0

		try:
			node_records = graph_manager.run_read("MATCH (n) RETURN count(n) AS total_nodes")
			relationship_records = graph_manager.run_read(
				"MATCH ()-[r]->() RETURN count(r) AS total_relationships"
			)
			total_nodes = int(node_records[0].get("total_nodes", 0)) if node_records else 0
			total_relationships = (
				int(relationship_records[0].get("total_relationships", 0))
				if relationship_records
				else 0
			)
			return total_nodes, total_relationships
		except Exception:
			logger.exception("Failed to fetch graph counts")
			return 0, 0

	def _evaluate_record(self, record: EvaluationRecord) -> RetrievalTestResult:
		logger.info(
			"Evaluating retrieval query [{}]: {}",
			self.backend.name,
			record.retrieval_query,
		)
		try:
			output = self.backend.retrieve(record.retrieval_query)
		except Exception as exc:
			logger.exception("Retrieval failed for query: {}", record.retrieval_query)
			return RetrievalTestResult(
				original_query=record.original_query,
				retrieval_query=record.retrieval_query,
				retrieved_context_summary="Retrieval failed.",
				precision_at_5=0.0,
				precision_at_10=0.0,
				recall_at_5=0.0,
				recall_at_10=0.0,
				ndcg_at_5=0.0,
				ndcg_at_10=0.0,
				average_similarity=0.0,
				average_similarity_original_query=0.0,
				average_similarity_retrieval_query=0.0,
				retrieval_time_ms=0.0,
				relevant_count=0,
				retrieved_count=0,
				remarks=f"Retrieval error: {exc}",
				hit_at_1=False,
				hit_at_3=False,
				hit_at_5=False,
			)

		return evaluate_retrieval_result(
			original_query=record.original_query,
			retrieval_query=record.retrieval_query,
			items=output.items,
			retrieval_time_ms=output.retrieval_time_ms,
			scorer=self.scorer,
			raw_retrieval=output.raw_context,
		)

	def run(self) -> EvaluationMetrics:
		"""Execute the full evaluation pipeline and write reports."""
		records = load_evaluation_dataset(self.config.dataset_path)
		logger.info(
			"Loaded {} evaluation records from {}",
			len(records),
			self.config.dataset_path,
		)

		results = [self._evaluate_record(record) for record in records]
		total_nodes, total_relationships = self._fetch_graph_counts()

		metrics = EvaluationMetrics(
			backend=self.backend.name,
			num_retrieval_tests=len(results),
			average_precision_at_5=sum(result.precision_at_5 for result in results) / len(results),
			average_precision_at_10=sum(result.precision_at_10 for result in results) / len(results),
			average_recall_at_5=sum(result.recall_at_5 for result in results) / len(results),
			average_recall_at_10=sum(result.recall_at_10 for result in results) / len(results),
			average_ndcg_at_5=sum(result.ndcg_at_5 for result in results) / len(results),
			average_ndcg_at_10=sum(result.ndcg_at_10 for result in results) / len(results),
			average_similarity=sum(result.average_similarity for result in results) / len(results),
			average_similarity_original_query=sum(result.average_similarity_original_query for result in results) / len(results),
			average_similarity_retrieval_query=sum(result.average_similarity_retrieval_query for result in results) / len(results),
			average_retrieval_time_ms=sum(result.retrieval_time_ms for result in results)
			/ len(results),
			total_nodes=total_nodes,
			total_relationships=total_relationships,
			relevance_threshold=self.scorer.relevance_threshold,
			embedding_provider=self.embedding_provider_name,
			average_hit_at_1=average_hit_rate(results, 1),
			average_hit_at_3=average_hit_rate(results, 3),
			average_hit_at_5=average_hit_rate(results, 5),
			similarity_distribution=aggregate_similarity_distribution(results),
			results=results,
		)

		self.config.results_dir.mkdir(parents=True, exist_ok=True)
		json_path = self.config.results_dir / f"{self.backend.name}.json"
		write_json_results(metrics, json_path)
		write_json_results(metrics, self.config.results_dir.parent / "results.json")
		write_markdown_report(
			metrics,
			self.config.markdown_report_path,
			title="Graph-Only Retrieval Baseline Evaluation",
		)

		try:
			self.backend.close()
		except Exception:
			logger.exception("Failed to close retrieval backend cleanly")

		logger.info(
			"Evaluation complete [{}]: P@5={:.3f}, Hit@5={:.3f}, avg similarity={:.3f}",
			self.backend.name,
			metrics.average_precision_at_5,
			metrics.average_hit_at_5,
			metrics.average_similarity,
		)
		return metrics
