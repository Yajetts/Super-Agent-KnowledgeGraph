"""Retrieval backend protocol for multi-backend evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetrievedItem:
	"""One retrieved context item used for metric computation."""

	item_id: str
	item_type: str
	text: str
	metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalOutput:
	"""Structured retrieval output from a backend."""

	query: str
	items: list[RetrievedItem]
	summary: str
	retrieval_time_ms: float
	raw_context: dict[str, Any] = field(default_factory=dict)


class RetrievalBackend(ABC):
	"""Interface implemented by graph-only, vector-only, and GraphRAG backends."""

	@property
	@abstractmethod
	def name(self) -> str:
		"""Return a stable backend identifier used in result filenames."""

	@abstractmethod
	def retrieve(self, query: str) -> RetrievalOutput:
		"""Execute retrieval for a query and return ordered context items."""

	def close(self) -> None:
		"""Release backend resources when evaluation completes."""
