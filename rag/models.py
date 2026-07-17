"""Data models for vector-based semantic retrieval."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VectorDocument(BaseModel):
    """Represent a document stored in the vector database."""

    document_id: str
    content: str
    source_type: str = Field(description="Type of source: finding, risk, or recommendation")
    source_agent: str = Field(description="Agent that generated this document")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(extra="forbid")


class SemanticContext(BaseModel):
    """Represent the result of a semantic search query."""

    documents: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    similarity_scores: list[float] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
