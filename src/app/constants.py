"""Constants module."""

import ssl
from os import environ

from faststream.security import SASLPlaintext

from app.utils import strtobool

KAFKA_BROKERS = environ.get("KAFKA_BROKERS")
KAFKA_SASL_AUTH_ENABLED = strtobool(environ.get("KAFKA_SASL_AUTH_ENABLED", "True"))
KAFKA_SASL_USER = environ.get("KAFKA_SASL_USER")
KAFKA_SASL_PASSWORD = environ.get("KAFKA_SASL_PASSWORD")

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
if KAFKA_SASL_AUTH_ENABLED:
    if not KAFKA_SASL_USER or not KAFKA_SASL_PASSWORD:
        raise ValueError(
            "Kafka SASL credentials are required when SASL auth is enabled"
        )
    security = SASLPlaintext(
        username=KAFKA_SASL_USER, password=KAFKA_SASL_PASSWORD, use_ssl=True
    )

TOPIC_USER = "user-events"
TOPIC_ARTICLE = "article-events"
TOPIC_ORDER = "order-events"
TOPIC_LOGIN = "login-events"
TOPIC_BUY = "buy-events"
TOPIC_SCROLL = "scroll-events"

OLLAMA_URL = environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = environ.get("OLLAMA_MODEL", "llama3")
REDIS_URL = environ.get("REDIS_URL", "redis://localhost:6379")
