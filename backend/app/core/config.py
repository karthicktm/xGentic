"""Application configuration with Pydantic settings."""

from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "xGentic API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000
    RELOAD: bool = False
    PUBLIC_URL: str | None = None

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "xgentic"
    DATABASE_URL: str | None = None

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str | None = None

    # Security
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Email (Resend)
    RESEND_API_KEY: str | None = None
    RESEND_FROM_EMAIL: str = "noreply@xgentic.com"
    FROM_EMAIL: str = "noreply@xgentic.com"
    FROM_NAME: str = "xGentic"
    FRONTEND_URL: str = "http://localhost:3000"
    EMAIL_VERIFICATION_REQUIRED: bool = True
    VERIFICATION_CODE_EXPIRY_MINUTES: int = 10

    # Super Admin
    SUPER_ADMIN_EMAIL: str | None = None
    SUPER_ADMIN_PASSWORD: str | None = None
    SUPER_ADMIN_NAME: str | None = None

    # Azure AI Foundry
    AZURE_TENANT_ID: str | None = None
    AZURE_CLIENT_ID: str | None = None
    AZURE_CLIENT_SECRET: str | None = None
    AZURE_FOUNDRY_ENDPOINT: str | None = None
    AZURE_FOUNDRY_API_KEY: str | None = None
    AZURE_SUBSCRIPTION_ID: str | None = None
    AZURE_RESOURCE_GROUP: str | None = None

    # Azure AD SSO
    AZURE_AD_TENANT_ID: str | None = None
    AZURE_AD_CLIENT_ID: str | None = None
    AZURE_AD_CLIENT_SECRET: str | None = None

    # OpenAI (for embeddings)
    OPENAI_API_KEY: str | None = None

    # Telephony
    TELEPHONY_PROVIDER: str = "telnyx"
    TELNYX_API_KEY: str | None = None
    TELNYX_PUBLIC_KEY: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    VONAGE_APPLICATION_ID: str | None = None
    VONAGE_PRIVATE_KEY: str | None = None
    VONAGE_API_KEY: str | None = None
    VONAGE_API_SECRET: str | None = None

    # External Service Timeouts (seconds)
    OPENAI_TIMEOUT: float = 30.0
    AZURE_TIMEOUT: float = 30.0
    TELNYX_TIMEOUT: float = 10.0
    TWILIO_TIMEOUT: float = 10.0
    VONAGE_TIMEOUT: float = 10.0
    DEFAULT_EXTERNAL_TIMEOUT: float = 30.0

    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0

    # Monitoring
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0

    # OpenTelemetry
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "xgentic-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

    # RAG / Knowledge Base
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_MAX_FILE_SIZE: int = 52428800  # 50MB
    RAG_MAX_DOCUMENTS_PER_AGENT: int = 50

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: Any) -> str:
        """Assemble database URL from components if not provided."""
        if v:
            # Convert postgres:// to postgresql+asyncpg://
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            return v

        values = info.data
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER', 'postgres')}"
            f":{values.get('POSTGRES_PASSWORD', 'postgres')}"
            f"@{values.get('POSTGRES_SERVER', 'localhost')}"
            f":{values.get('POSTGRES_PORT', 5432)}"
            f"/{values.get('POSTGRES_DB', 'xgentic')}"
        )

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: str | None, info: Any) -> str:
        """Assemble Redis URL from components if not provided."""
        if v:
            return v

        values = info.data
        password = values.get("REDIS_PASSWORD")
        host = values.get("REDIS_HOST", "localhost")
        port = values.get("REDIS_PORT", 6379)
        db = values.get("REDIS_DB", 0)

        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
