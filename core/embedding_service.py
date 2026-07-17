"""Embedding service for generating text embeddings using OpenAI."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from loguru import logger
from openai import OpenAI

from config.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import Sequence


class EmbeddingService:
    """Service for generating embeddings using OpenAI's text-embedding models."""

    def __init__(self) -> None:
        """Initialize the embedding service with OpenAI client."""
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._model = settings.embedding_model
        self._base_url = settings.openai_base_url

        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        client_kwargs = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url

        self._client = OpenAI(**client_kwargs)
        logger.info("EmbeddingService initialized with model: {}", self._model)

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of float values representing the embedding vector.

        Raises:
            RuntimeError: If the embedding generation fails.
        """
        try:
            logger.debug("Generating embedding for text (length: {})", len(text))
            response = self._client.embeddings.create(
                model=self._model,
                input=text,
            )
            embedding = response.data[0].embedding
            logger.debug("Embedding generated successfully (dimension: {})", len(embedding))
            return embedding
        except Exception as exc:
            logger.error("Failed to generate embedding: {}", exc)
            raise RuntimeError(f"Embedding generation failed: {exc}") from exc

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for multiple text documents.

        Args:
            texts: A sequence of text strings to embed.

        Returns:
            A list of embedding vectors, one for each input text.

        Raises:
            RuntimeError: If the embedding generation fails.
        """
        try:
            logger.info("Generating embeddings for {} documents", len(texts))
            response = self._client.embeddings.create(
                model=self._model,
                input=list(texts),
            )
            embeddings = [item.embedding for item in response.data]
            logger.info("Successfully generated {} embeddings", len(embeddings))
            return embeddings
        except Exception as exc:
            logger.error("Failed to generate embeddings for documents: {}", exc)
            raise RuntimeError(f"Document embedding generation failed: {exc}") from exc


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Return a cached embedding service instance."""
    return EmbeddingService()
