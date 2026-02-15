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

TOPIC_MEDIA_RADIO = "media-radio-test"
TOPIC_MEDIA_TV = "media-tv-test"
TOPIC_SALE = "sale-test"
