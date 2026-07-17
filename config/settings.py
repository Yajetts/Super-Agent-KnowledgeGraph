"""Centralized application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="superagent_kg", alias="POSTGRES_DB")
    chroma_db_path: str = Field(default="./data/chroma", alias="CHROMA_DB_PATH")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Dynamic Agent Configuration
    min_agent_similarity: float = Field(default=0.30, alias="MIN_AGENT_SIMILARITY")
    max_dynamic_agents_per_task: int = Field(default=5, alias="MAX_DYNAMIC_AGENTS_PER_TASK")
    agent_deduplication_threshold: float = Field(default=0.80, alias="AGENT_DEDUPLICATION_THRESHOLD")

    # Output Quality Limits
    max_findings_per_task: int = Field(default=10, alias="MAX_FINDINGS_PER_TASK")
    max_risks_per_task: int = Field(default=10, alias="MAX_RISKS_PER_TASK")
    max_recommendations_per_task: int = Field(default=10, alias="MAX_RECOMMENDATIONS_PER_TASK")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance after loading environment values."""
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=project_root / ".env", override=False)
    return Settings()
