from functools import lru_cache
from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_env: str = "development"
    app_name: str = "Async RAG API"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ragdb"
    redis_url: str = "redis://localhost:6379/0"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_dimension: int = Field(default=1536, gt=0)
    embedding_concurrency: int = Field(default=8, gt=0)
    embedding_timeout_seconds: float = Field(default=20, gt=0)
    chunk_size: int = Field(default=800, gt=0)
    chunk_overlap: int = Field(default=100, ge=0)
    top_k: int = Field(default=5, gt=0, le=20)
    vector_weight: float = Field(default=.7, ge=0, le=1)
    keyword_weight: float = Field(default=.3, ge=0, le=1)
    min_retrieval_score: float = Field(default=.3, ge=0, le=1)
    redis_cache_ttl: int = Field(default=300, gt=0)
    rate_limit_capacity: int = Field(default=100, gt=0)
    rate_limit_refill_rate: float = Field(default=10, gt=0)
    db_pool_size: int = Field(default=20, gt=0)
    db_max_overflow: int = Field(default=20, ge=0)
    db_pool_timeout: int = Field(default=30, gt=0)
    max_document_chars: int = Field(default=1_000_000, gt=0)
    max_query_chars: int = Field(default=4_000, gt=0)

    @model_validator(mode="after")
    def validate_chunking(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.vector_weight + self.keyword_weight <= 0:
            raise ValueError("retrieval weights must have a positive sum")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
