"""Main application module."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.confluent import KafkaBroker
from faststream.confluent.config import ConfluentConfig  # type: ignore # pylint: disable=import-error,no-name-in-module

from app.constants import KAFKA_CONFIG, KAFKA_BROKERS, SECURITY
from app.service.routers import router, shutdown_fraud_service


logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

broker = KafkaBroker(
    bootstrap_servers=KAFKA_BROKERS or "localhost:9092",
    security=SECURITY,
    config=ConfluentConfig(KAFKA_CONFIG),
)

broker.include_router(router)


class FKLStreamerApp(FastAPI):
    """FKL Streamer Application."""

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super().__init__(*args, **kwargs)


@asynccontextmanager
async def lifespan(_app: FKLStreamerApp):
    """Handle application lifespan."""
    await broker.start()
    yield
    await broker.close()
    await shutdown_fraud_service()


app = FKLStreamerApp(
    title="FKLStreamerApp",
    description="FKLStreamerApp",
    version="0.3.0",
    contact="Stef",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    """Check application health."""
    return {"status": "healthy"}
