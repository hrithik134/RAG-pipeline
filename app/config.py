"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

import json
from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="RAG Pipeline", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: Literal["development", "production", "testing"] = Field(
        default="development", alias="APP_ENV"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")

    # Database
    database_url: str = Field(
        default="postgresql://rag_user:rag_password@postgres:5432/rag_db",
        alias="DATABASE_URL",
    )
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Pinecone
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_environment: str = Field(
        default="us-east-1-aws", alias="PINECONE_ENVIRONMENT"
    )
    pinecone_index_name: str = Field(
        default="ragingestion", alias="PINECONE_INDEX_NAME"
    )
    pinecone_dimension: int = Field(default=3072, alias="PINECONE_DIMENSION")
    pinecone_metric: Literal["cosine", "euclidean", "dotproduct"] = Field(
        default="cosine", alias="PINECONE_METRIC"
    )
    pinecone_cloud: Literal["aws", "gcp", "azure"] = Field(
        default="aws", alias="PINECONE_CLOUD"
    )
    pinecone_region: str = Field(
        default="us-east-1", alias="PINECONE_REGION"
    )

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-large", alias="OPENAI_EMBEDDING_MODEL"
    )
    openai_max_tokens: int = Field(default=2048, alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.1, alias="OPENAI_TEMPERATURE")

    # Google AI
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_model: str = Field(default="gemini-2.5-pro", alias="GOOGLE_MODEL")
    google_embedding_model: str = Field(
        default="models/text-embedding-004", alias="GOOGLE_EMBEDDING_MODEL"
    )
    google_temperature: float = Field(default=0.1, alias="GOOGLE_TEMPERATURE")
    google_max_tokens: int = Field(default=2048, alias="GOOGLE_MAX_TOKENS")

    # Provider Selection
    llm_provider: Literal["openai", "google"] = Field(
        default="openai", alias="LLM_PROVIDER"
    )
    embedding_provider: Literal["openai", "google", "vertex"] = Field(
        default="openai", alias="EMBEDDING_PROVIDER"
    )
    
    # Embedding Configuration
    embed_batch_size: int = Field(default=64, alias="EMBED_BATCH_SIZE")
    upsert_batch_size: int = Field(default=100, alias="UPSERT_BATCH_SIZE")
    index_concurrency: int = Field(default=2, alias="INDEX_CONCURRENCY")
    embed_retry_max: int = Field(default=5, alias="EMBED_RETRY_MAX")
    embed_retry_delay: float = Field(default=1.0, alias="EMBED_RETRY_DELAY")

    # Document Processing
    docsenabled: bool = Field(default=True, alias="DOCS_ENABLED")
    max_documents_per_upload: int = Field(
        default=20, alias="MAX_DOCUMENTS_PER_UPLOAD"
    )
    max_pages_per_document: int = Field(default=1000, alias="MAX_PAGES_PER_DOCUMENT")
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    allowed_extensions: str = Field(default="pdf,docx,txt,md", alias="ALLOWED_EXTENSIONS")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    # Chunking
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    min_chunk_size: int = Field(default=100, alias="MIN_CHUNK_SIZE")

    # RAG Configuration
    rag_top_k: int = Field(default=10, alias="RAG_TOP_K")
    rag_mmr_lambda: float = Field(default=0.5, alias="RAG_MMR_LAMBDA")
    rag_max_context_tokens: int = Field(default=6000, alias="RAG_MAX_CONTEXT_TOKENS")
    rag_temperature: float = Field(default=0.1, alias="RAG_TEMPERATURE")

    # Retrieval Configuration
    retrieval_method: Literal["semantic", "keyword", "hybrid"] = Field(
        default="hybrid", alias="RETRIEVAL_METHOD"
    )
    retrieval_top_k: int = Field(default=10, alias="RETRIEVAL_TOP_K")
    mmr_lambda: float = Field(default=0.5, alias="MMR_LAMBDA")
    use_hybrid_search: bool = Field(default=True, alias="USE_HYBRID_SEARCH")
    bm25_k1: float = Field(default=1.2, alias="BM25_K1")
    bm25_b: float = Field(default=0.75, alias="BM25_B")
    rrf_k: int = Field(default=60, alias="RRF_K")

    # LLM Configuration
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    llm_timeout_seconds: int = Field(default=30, alias="LLM_TIMEOUT_SECONDS")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, alias="RATE_LIMIT_PERIOD")
    rate_limit_storage_url: str = Field(
        default="redis://localhost:6379/0", 
        alias="RATE_LIMIT_STORAGE_URL"
    )
    
    # Rate limit strings for different endpoint types
    rate_limit_upload: str = Field(default="10/hour", alias="RATE_LIMIT_UPLOAD")
    rate_limit_query: str = Field(default="20/minute", alias="RATE_LIMIT_QUERY")
    rate_limit_read: str = Field(default="100/minute", alias="RATE_LIMIT_READ")
    rate_limit_delete: str = Field(default="20/minute", alias="RATE_LIMIT_DELETE")
    rate_limit_health: str = Field(default="300/minute", alias="RATE_LIMIT_HEALTH")
    rate_limit_metrics: str = Field(default="30/minute", alias="RATE_LIMIT_METRICS")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # Background Tasks
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND"
    )

    # Monitoring
    enable_metrics: bool = Field(default=False, alias="ENABLE_METRICS")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")

    # Cloud Storage
    use_cloud_storage: bool = Field(default=False, alias="USE_CLOUD_STORAGE")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: str = Field(default="", alias="AWS_S3_BUCKET")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convert comma-separated extensions to list with dots."""
        extensions = [ext.strip().lower() for ext in self.allowed_extensions.split(",")]
        # Ensure all extensions start with a dot
        return [f".{ext}" if not ext.startswith(".") else ext for ext in extensions]

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.cors_origins, str):
            # Try to parse as JSON first (for backward compatibility)
            try:
                parsed = json.loads(self.cors_origins)
                if isinstance(parsed, list):
                    return [origin.strip() for origin in parsed]
            except json.JSONDecodeError:
                pass
            # Fallback to comma-separated
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env == "development"

    @property
    def upload_directory(self) -> str:
        """Alias for upload_dir for backward compatibility."""
        return self.upload_dir
    
    @property
    def UPLOAD_DIR(self) -> str:
        """Uppercase alias for upload_dir."""
        return self.upload_dir


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()