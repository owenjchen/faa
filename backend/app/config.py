"""Application configuration management."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Fidelity Agent Assistant"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql://faa:faa@localhost:5432/faa"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # LLM - Azure OpenAI
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_TEMPERATURE: float = 0.7
    AZURE_OPENAI_MAX_TOKENS: int = 2000

    # LLM - AWS Bedrock (optional)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Vector Store - OpenSearch (AWS)
    OPENSEARCH_HOST: Optional[str] = None
    OPENSEARCH_PORT: int = 443
    OPENSEARCH_USERNAME: Optional[str] = None
    OPENSEARCH_PASSWORD: Optional[str] = None
    OPENSEARCH_USE_SSL: bool = True
    OPENSEARCH_VERIFY_CERTS: bool = True
    OPENSEARCH_INDEX_NAME: str = "faa_knowledge_base"
    OPENSEARCH_VECTOR_FIELD: str = "embedding"
    OPENSEARCH_TEXT_FIELD: str = "content"
    OPENSEARCH_METADATA_FIELD: str = "metadata"

    # Search Configuration
    SEARCH_TOP_K: int = 5
    SEARCH_TIMEOUT: int = 10  # seconds
    FIDELITY_SEARCH_URL: str = "https://www.fidelity.com"
    MYGPS_API_URL: Optional[str] = None
    MYGPS_API_KEY: Optional[str] = None

    # Evaluation Thresholds
    EVALUATION_MIN_SCORE: int = 3  # 1-5 scale
    EVALUATION_MAX_RETRIES: int = 3

    # Audio/Transcription
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    AUDIO_SAMPLE_RATE: int = 16000

    # Langfuse Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://langfuse.fmr.com"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
