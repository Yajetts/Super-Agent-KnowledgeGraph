"""Tests for the retrieval evaluation framework."""

from __future__ import annotations

from pathlib import Path

from evaluation.backends.base import RetrievalOutput, RetrievedItem
from evaluation.dataset import load_evaluation_dataset
from evaluation.metrics import (
	compute_similarity_distribution,
	evaluate_retrieval_result,
	hit_at_k,
	precision_at_k,
	similarity_bucket_label,
)
from evaluation.similarity import SimilarityScorer, TfidfEmbeddingProvider


class _StubBackend:
	name = "stub"

	def __init__(self, items: list[RetrievedItem]) -> None:
		self._items = items

	def retrieve(self, query: str) -> RetrievalOutput:
		return RetrievalOutput(
			query=query,
			items=self._items,
			summary="Stub summary",
			retrieval_time_ms=12.5,
		)


def test_precision_at_k() -> None:
	assert precision_at_k([True, False, True, True], 4) == 0.75
	assert precision_at_k([], 5) == 0.0


def test_dataset_loads_27_records() -> None:
	root = Path(__file__).resolve().parents[1]
	records = load_evaluation_dataset(root / "docs" / "retr_data.txt")
	assert len(records) == 27


def test_evaluate_retrieval_result_with_local_embeddings() -> None:
	scorer = SimilarityScorer(provider=TfidfEmbeddingProvider(), relevance_threshold=0.1)
	items = [
		RetrievedItem(
			item_id="finding:1",
			item_type="finding",
			text="Autonomous vehicle safety risks and regulatory challenges",
		),
		RetrievedItem(
			item_id="finding:2",
			item_type="finding",
			text="Unrelated quantum computing startup funding trends",
		),
	]
	result = evaluate_retrieval_result(
		original_query="Assess risks of autonomous vehicles",
		retrieval_query="List advantages and disadvantages of autonomous vehicles",
		items=items,
		retrieval_time_ms=10.0,
		scorer=scorer,
	)
	assert result.retrieved_count == 2
	assert result.precision_at_5 >= 0.0
	assert result.average_similarity >= 0.0


def test_similarity_bucket_label() -> None:
	assert similarity_bucket_label(0.0) == "0.0-0.1"
	assert similarity_bucket_label(0.09) == "0.0-0.1"
	assert similarity_bucket_label(0.1) == "0.1-0.2"
	assert similarity_bucket_label(0.95) == "0.9-1.0"
	assert similarity_bucket_label(1.0) == "0.9-1.0"


def test_compute_similarity_distribution() -> None:
	distribution = compute_similarity_distribution([0.05, 0.15, 0.95, 0.95])
	assert distribution["0.0-0.1"] == 1
	assert distribution["0.1-0.2"] == 1
	assert distribution["0.9-1.0"] == 2


def test_hit_at_k_matches_original_task_query() -> None:
	items = [
		RetrievedItem(
			item_id="task:1",
			item_type="task",
			text="Analyze renewable energy markets (business_analysis)",
		),
		RetrievedItem(
			item_id="task:2",
			item_type="task",
			text="Assess risks of autonomous vehicles (risk_assessment)",
		),
	]
	assert hit_at_k("Assess risks of autonomous vehicles", items, 1) is False
	assert hit_at_k("Assess risks of autonomous vehicles", items, 2) is True
	assert hit_at_k("Assess risks of autonomous vehicles", items, 5) is True
