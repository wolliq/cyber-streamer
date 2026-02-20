"""Constants module."""

import ssl

# pylint: disable=invalid-name

from faststream.security import SASLPlaintext
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    KAFKA_BROKERS: str = "localhost:9092"
    KAFKA_SASL_AUTH_ENABLED: bool = True
    KAFKA_SASL_USER: str | None = None
    KAFKA_SASL_PASSWORD: str | None = None

    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:latest"
    REDIS_URL: str = "redis://localhost:6379"
    HUGGING_FACE_HUB_TOKEN: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

KAFKA_CONFIG: dict = {
    "api.version.request": "true",
    "broker.version.fallback": "0.10.0.0",
    "api.version.fallback.ms": 0,
    "client.id": "media-channels-client",
    "group.id": "media-channels-group",
    "auto.offset.reset": "earliest",
}

SSL_CONTEXT = ssl.create_default_context()
SECURITY = None
if settings.KAFKA_SASL_AUTH_ENABLED:
    if not settings.KAFKA_SASL_USER or not settings.KAFKA_SASL_PASSWORD:
        raise ValueError(
            "Kafka SASL credentials are required when SASL auth is enabled"
        )
    SECURITY = SASLPlaintext(
        username=settings.KAFKA_SASL_USER,
        password=settings.KAFKA_SASL_PASSWORD,
        use_ssl=True,
    )

TOPIC_USER = "user-events"
TOPIC_ARTICLE = "article-events"
TOPIC_ORDER = "order-events"
TOPIC_LOGIN = "login-events"
TOPIC_BUY = "buy-events"
TOPIC_SCROLL = "scroll-events"
