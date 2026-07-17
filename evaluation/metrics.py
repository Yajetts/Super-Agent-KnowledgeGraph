"""Retrieval evaluation metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from evaluation.backends.base import RetrievedItem
from evaluation.similarity import SimilarityScorer


@dataclass(frozen=True)
class ItemScore:
	"""Similarity score for one retrieved item."""

	item_id: str
	item_type: str
	text: str
	similarity: float
	is_relevant: bool


@dataclass(frozen=True)
class RetrievalTestResult:
	"""Metrics for one original/retrieval query pair."""

	original_query: str
	retrieval_query: str
	retrieved_context_summary: str
	precision_at_5: float
	precision_at_10: float
	recall_at_5: float
	recall_at_10: float
	ndcg_at_5: float
	ndcg_at_10: float
	average_similarity: float
	average_similarity_original_query: float
	average_similarity_retrieval_query: float
	retrieval_time_ms: float
	relevant_count: int
	retrieved_count: int
	remarks: str
	hit_at_1: bool = False
	hit_at_3: bool = False
	hit_at_5: bool = False
	item_scores: list[ItemScore] = field(default_factory=list)
	raw_retrieval: dict[str, Any] = field(default_factory=dict)

	def to_dict(self) -> dict[str, Any]:
		payload = asdict(self)
		payload["item_scores"] = [asdict(score) for score in self.item_scores]
		return payload


@dataclass(frozen=True)
class EvaluationMetrics:
	"""Aggregate metrics across all retrieval tests."""

	backend: str
	num_retrieval_tests: int
	average_precision_at_5: float
	average_precision_at_10: float
	average_recall_at_5: float
	average_recall_at_10: float
	average_ndcg_at_5: float
	average_ndcg_at_10: float
	average_similarity: float
	average_similarity_original_query: float
	average_similarity_retrieval_query: float
	average_retrieval_time_ms: float
	total_nodes: int
	total_relationships: int
	relevance_threshold: float
	embedding_provider: str
	average_hit_at_1: float = 0.0
	average_hit_at_3: float = 0.0
	average_hit_at_5: float = 0.0
	similarity_distribution: dict[str, int] = field(default_factory=dict)
	results: list[RetrievalTestResult] = field(default_factory=list)

	def to_dict(self) -> dict[str, Any]:
		return {
			"backend": self.backend,
			"aggregate": {
				"num_retrieval_tests": self.num_retrieval_tests,
				"average_precision_at_5": self.average_precision_at_5,
				"average_precision_at_10": self.average_precision_at_10,
				"average_recall_at_5": self.average_recall_at_5,
				"average_recall_at_10": self.average_recall_at_10,
				"average_ndcg_at_5": self.average_ndcg_at_5,
				"average_ndcg_at_10": self.average_ndcg_at_10,
				"average_similarity": self.average_similarity,
				"average_similarity_original_query": self.average_similarity_original_query,
				"average_similarity_retrieval_query": self.average_similarity_retrieval_query,
				"average_retrieval_time_ms": self.average_retrieval_time_ms,
				"total_nodes": self.total_nodes,
				"total_relationships": self.total_relationships,
				"relevance_threshold": self.relevance_threshold,
				"embedding_provider": self.embedding_provider,
				"average_hit_at_1": self.average_hit_at_1,
				"average_hit_at_3": self.average_hit_at_3,
				"average_hit_at_5": self.average_hit_at_5,
				"similarity_distribution": self.similarity_distribution,
			},
			"results": [result.to_dict() for result in self.results],
		}


def precision_at_k(relevance_flags: Sequence[bool], k: int) -> float:
	"""Compute precision@K from binary relevance flags."""
	if k <= 0:
		return 0.0

	top_k = list(relevance_flags[:k])
	if not top_k:
		return 0.0

	relevant = sum(1 for flag in top_k if flag)
	return relevant / len(top_k)


def recall_at_k(relevance_flags: Sequence[bool], k: int) -> float:
	"""Compute recall@K from binary relevance flags."""
	if k <= 0:
		return 0.0

	top_k = list(relevance_flags[:k])
	if not top_k:
		return 0.0

	total_relevant = sum(1 for flag in relevance_flags if flag)
	if total_relevant == 0:
		return 0.0

	relevant_in_top_k = sum(1 for flag in top_k if flag)
	return relevant_in_top_k / total_relevant


def ndcg_at_k(relevance_flags: Sequence[bool], k: int) -> float:
	"""Compute normalized discounted cumulative gain at K.
	
	Uses binary relevance (1 for relevant, 0 for irrelevant).
	DCG = sum(relevance_i / log2(i+1)) for i in 1..k
	IDCG = sum(1 / log2(i+1)) for i in 1..total_relevant
	nDCG = DCG / IDCG
	"""
	if k <= 0:
		return 0.0

	import math

	top_k = list(relevance_flags[:k])
	if not top_k:
		return 0.0

	# Compute DCG
	dcg = 0.0
	for i, relevant in enumerate(top_k, start=1):
		if relevant:
			dcg += 1.0 / math.log2(i + 1)

	# Compute IDCG (ideal DCG - all relevant items at top)
	total_relevant = sum(1 for flag in relevance_flags if flag)
	if total_relevant == 0:
		return 0.0

	idcg = 0.0
	for i in range(1, min(k, total_relevant) + 1):
		idcg += 1.0 / math.log2(i + 1)

	if idcg == 0.0:
		return 0.0

	return dcg / idcg


def average_similarity(similarities: Sequence[float]) -> float:
	"""Compute mean semantic similarity across retrieved items."""
	if not similarities:
		return 0.0
	return sum(similarities) / len(similarities)


SIMILARITY_BUCKET_LABELS: tuple[str, ...] = tuple(
	f"{index / 10:.1f}-{index / 10 + 0.1:.1f}" for index in range(10)
)


def similarity_bucket_label(score: float) -> str:
	"""Map a cosine similarity score to a histogram bucket label."""
	clamped = max(0.0, min(1.0, score))
	if clamped >= 0.9:
		return SIMILARITY_BUCKET_LABELS[-1]
	bucket_index = int(clamped * 10)
	return SIMILARITY_BUCKET_LABELS[bucket_index]


def compute_similarity_distribution(similarities: Sequence[float]) -> dict[str, int]:
	"""Count similarity scores across fixed-width histogram buckets."""
	distribution = {label: 0 for label in SIMILARITY_BUCKET_LABELS}
	for score in similarities:
		distribution[similarity_bucket_label(score)] += 1
	return distribution


def aggregate_similarity_distribution(results: Sequence[RetrievalTestResult]) -> dict[str, int]:
	"""Aggregate item-level similarity scores across all retrieval tests."""
	all_scores = [
		item_score.similarity
		for result in results
		for item_score in result.item_scores
	]
	return compute_similarity_distribution(all_scores)


def _normalize_query(query: str) -> str:
	return query.strip().lower()


def _task_query_from_item(item: RetrievedItem) -> str:
	text = item.text.strip()
	if " (" in text and text.endswith(")"):
		return text.rsplit(" (", 1)[0].strip()
	return text


def _related_tasks_from_raw_retrieval(raw_retrieval: dict[str, Any]) -> list[dict[str, Any]]:
	tasks = raw_retrieval.get("related_tasks", [])
	if not isinstance(tasks, list):
		return []
	return [task for task in tasks if isinstance(task, dict)]


def hit_at_k(relevance_flags: Sequence[bool], k: int) -> bool:
	"""Return True when at least one relevant item appears in the top-K results.
	
	This is the standard retrieval Hit@K metric, which measures whether the retrieval
	system successfully retrieves at least one relevant item within the top-k results.
	"""
	if k <= 0:
		return False

	top_k = list(relevance_flags[:k])
	if not top_k:
		return False

	return any(flag for flag in top_k)


def average_hit_rate(results: Sequence[RetrievalTestResult], k: int) -> float:
	"""Compute the mean Hit@K rate across retrieval tests."""
	if not results:
		return 0.0

	attribute = {1: "hit_at_1", 3: "hit_at_3", 5: "hit_at_5"}[k]
	hits = sum(1 for result in results if getattr(result, attribute))
	return hits / len(results)


def build_remarks(
	precision_at_5: float,
	precision_at_10: float,
	average_score: float,
	relevant_count: int,
	retrieved_count: int,
) -> str:
	"""Generate a short automatic remark for a retrieval test."""
	if retrieved_count == 0:
		return "No items retrieved."

	if precision_at_5 >= 0.8 and average_score >= 0.75:
		return "Strong retrieval quality with high semantic alignment to the original task."

	if precision_at_5 >= 0.5:
		return "Moderate retrieval quality; retrieved context partially aligns with the original task."

	if relevant_count == 0:
		return "Weak retrieval quality; no retrieved items met the relevance threshold."

	return "Low retrieval quality; retrieved context has limited semantic overlap with the original task."


def summarize_retrieved_context(items: Sequence[RetrievedItem], max_chars: int = 220) -> str:
	"""Build a concise summary from retrieved graph nodes."""
	if not items:
		return "No retrieved context."

	type_counts: dict[str, int] = {}
	snippets: list[str] = []
	for item in items:
		type_counts[item.item_type] = type_counts.get(item.item_type, 0) + 1
		if len(snippets) < 3:
			snippets.append(item.text.strip())

	count_parts = [
		f"{count} {item_type}{'s' if count != 1 else ''}"
		for item_type, count in sorted(type_counts.items())
	]
	summary = f"Retrieved {', '.join(count_parts)}"
	if snippets:
		summary += f"; highlights: {'; '.join(snippets)}"

	if len(summary) > max_chars:
		return summary[: max_chars - 3].rstrip() + "..."
	return summary


def evaluate_retrieval_result(
	original_query: str,
	retrieval_query: str,
	items: Sequence[RetrievedItem],
	retrieval_time_ms: float,
	scorer: SimilarityScorer,
	summary: str | None = None,
	raw_retrieval: dict[str, Any] | None = None,
) -> RetrievalTestResult:
	"""Compute automatic relevance metrics for one retrieval test."""
	item_texts = [item.text for item in items]
	
	# Compute similarity against both original_query and retrieval_query
	similarities_original = scorer.score_items(original_query, item_texts)
	similarities_retrieval = scorer.score_items(retrieval_query, item_texts)
	
	# Use percentile-based relevance determination
	relevance_flags = scorer.compute_relevance_flags(similarities_original)
	
	item_scores = [
		ItemScore(
			item_id=item.item_id,
			item_type=item.item_type,
			text=item.text,
			similarity=similarity,
			is_relevant=relevance_flag,
		)
		for item, similarity, relevance_flag in zip(items, similarities_original, relevance_flags, strict=True)
	]

	relevant_count = sum(relevance_flags)
	retrieved_count = len(item_scores)
	avg_similarity = average_similarity(similarities_original)
	avg_similarity_original = average_similarity(similarities_original)
	avg_similarity_retrieval = average_similarity(similarities_retrieval)
	
	p_at_5 = precision_at_k(relevance_flags, 5)
	p_at_10 = precision_at_k(relevance_flags, 10)
	r_at_5 = recall_at_k(relevance_flags, 5)
	r_at_10 = recall_at_k(relevance_flags, 10)
	ndcg_5 = ndcg_at_k(relevance_flags, 5)
	ndcg_10 = ndcg_at_k(relevance_flags, 10)
	
	raw_context = raw_retrieval or {}

	return RetrievalTestResult(
		original_query=original_query,
		retrieval_query=retrieval_query,
		retrieved_context_summary=summary or summarize_retrieved_context(items),
		precision_at_5=p_at_5,
		precision_at_10=p_at_10,
		recall_at_5=r_at_5,
		recall_at_10=r_at_10,
		ndcg_at_5=ndcg_5,
		ndcg_at_10=ndcg_10,
		average_similarity=avg_similarity,
		average_similarity_original_query=avg_similarity_original,
		average_similarity_retrieval_query=avg_similarity_retrieval,
		retrieval_time_ms=retrieval_time_ms,
		relevant_count=relevant_count,
		retrieved_count=retrieved_count,
		remarks=build_remarks(
			precision_at_5=p_at_5,
			precision_at_10=p_at_10,
			average_score=avg_similarity,
			relevant_count=relevant_count,
			retrieved_count=retrieved_count,
		),
		hit_at_1=hit_at_k(relevance_flags, 1),
		hit_at_3=hit_at_k(relevance_flags, 3),
		hit_at_5=hit_at_k(relevance_flags, 5),
		item_scores=item_scores,
		raw_retrieval=raw_context,
	)
