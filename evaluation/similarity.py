"""Embedding generation and cosine similarity utilities."""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Sequence

from loguru import logger


def cosine_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
    """Compute cosine similarity between two dense vectors."""
    if len(vector_a) != len(vector_b) or not vector_a:
        return 0.0

    dot_product = sum(left * right for left, right in zip(vector_a, vector_b, strict=True))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class EmbeddingProvider(ABC):
    """Abstract embedding provider used by the evaluation metrics."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""


class TfidfEmbeddingProvider(EmbeddingProvider):
    """Local TF-IDF embeddings for reproducible offline evaluation."""

    def __init__(self) -> None:
        self._vocabulary: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._fitted = False

    def _build_vocabulary(self, texts: Sequence[str]) -> None:
        documents = [_tokenize(text) for text in texts]
        document_frequency: Counter[str] = Counter()
        for tokens in documents:
            document_frequency.update(set(tokens))

        self._vocabulary = {
            token: index for index, token in enumerate(sorted(document_frequency))
        }
        document_count = max(len(documents), 1)
        self._idf = {
            token: math.log((1 + document_count) / (1 + frequency)) + 1.0
            for token, frequency in document_frequency.items()
        }
        self._fitted = True

    def _vectorize(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        term_frequency: Counter[str] = Counter(tokens)
        vector = [0.0] * len(self._vocabulary)
        for token, count in term_frequency.items():
            index = self._vocabulary.get(token)
            if index is None:
                continue
            vector[index] = float(count) * self._idf.get(token, 1.0)
        return vector

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        if not self._fitted:
            self._build_vocabulary(texts)

        unknown_tokens = {
            token
            for text in texts
            for token in _tokenize(text)
            if token not in self._vocabulary
        }
        if unknown_tokens:
            expanded_texts = list(texts)
            expanded_texts.extend(unknown_tokens)
            self._build_vocabulary(expanded_texts)

        return [self._vectorize(text) for text in texts]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider used when an API key is configured."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        from openai import OpenAI

        from config.settings import get_settings

        settings = get_settings()
        self._model = model
        self._client = OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        cleaned = [text if text.strip() else "empty" for text in texts]
        vectors: list[list[float]] = []
        batch_size = 64
        for start in range(0, len(cleaned), batch_size):
            batch = cleaned[start : start + batch_size]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            vectors.extend(item.embedding for item in response.data)
        return vectors


def create_embedding_provider(prefer_openai: bool = True) -> EmbeddingProvider:
    """Create the best available embedding provider for the current environment."""
    if prefer_openai:
        from config.settings import get_settings

        settings = get_settings()
        if settings.openai_api_key.strip():
            try:
                logger.info("Using OpenAI embeddings for evaluation")
                return OpenAIEmbeddingProvider()
            except Exception:
                logger.exception("Failed to initialize OpenAI embeddings; falling back to TF-IDF")

    logger.info("Using TF-IDF embeddings for evaluation")
    return TfidfEmbeddingProvider()


def compute_relevance_by_percentile(similarities: Sequence[float], percentile: float = 50.0) -> list[bool]:
	"""Compute relevance flags using percentile-based ranking within a query.
	
	Items with similarity scores in the top percentile are considered relevant.
	This adapts to the actual similarity distribution and is more robust than fixed thresholds.
	
	Args:
		similarities: List of similarity scores for retrieved items
		percentile: Percentile threshold (0-100). Items above this percentile are relevant.
	
	Returns:
		List of boolean relevance flags corresponding to each similarity score
	"""
	if not similarities:
		return []
	
	import numpy as np
	
	threshold = float(np.percentile(similarities, percentile))
	return [sim >= threshold for sim in similarities]


class SimilarityScorer:
    """Compute semantic similarity scores between a query and retrieved items."""

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        relevance_threshold: float = 0.75,
        use_percentile_relevance: bool = True,
        relevance_percentile: float = 50.0,
    ) -> None:
        self.provider = provider or create_embedding_provider()
        self.relevance_threshold = relevance_threshold
        self.use_percentile_relevance = use_percentile_relevance
        self.relevance_percentile = relevance_percentile

    def score_items(
        self,
        reference_query: str,
        item_texts: Sequence[str],
    ) -> list[float]:
        """Return cosine similarity between the reference query and each item."""
        if not item_texts:
            return []

        texts = [reference_query, *item_texts]
        try:
            embeddings = self.provider.embed(texts)
        except Exception:
            logger.exception("Embedding provider failed; falling back to TF-IDF for this scoring batch")
            fallback = TfidfEmbeddingProvider()
            fallback._build_vocabulary(texts)
            embeddings = fallback.embed(texts)

        reference_vector = embeddings[0]
        return [cosine_similarity(reference_vector, vector) for vector in embeddings[1:]]

    def is_relevant(self, similarity: float) -> bool:
        """Return True when an item meets the configured relevance threshold."""
        return similarity >= self.relevance_threshold

    def compute_relevance_flags(self, similarities: Sequence[float]) -> list[bool]:
        """Compute relevance flags for a list of similarities using the configured method."""
        if self.use_percentile_relevance:
            return compute_relevance_by_percentile(similarities, self.relevance_percentile)
        return [sim >= self.relevance_threshold for sim in similarities]