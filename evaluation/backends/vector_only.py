"""Vector-only retrieval backend placeholder for future ChromaDB evaluation."""

from __future__ import annotations

from evaluation.backends.base import RetrievalBackend, RetrievalOutput


class VectorOnlyBackend(RetrievalBackend):
	"""Placeholder backend for Phase 7 vector retrieval evaluation."""

	@property
	def name(self) -> str:
		return "vector_only"

	def retrieve(self, query: str) -> RetrievalOutput:
		raise NotImplementedError(
			"VectorOnlyBackend is not implemented yet. "
			"Implement ChromaDB retrieval before running vector-only evaluation."
		)
