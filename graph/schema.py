"""Graph schema models for future Neo4j integration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraphNode(BaseModel):
    """Represent a node in the knowledge graph."""

    id: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class GraphRelationship(BaseModel):
    """Represent a relationship between two graph nodes."""

    source_id: str
    target_id: str
    relation_type: str
    properties: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")
