"""Main application module."""

import logging

from typing import cast
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.confluent import KafkaBroker
from faststream.confluent.helpers.config import ConfluentConfig  # type: ignore # pylint: disable=import-error,no-name-in-module

from app.constants import KAFKA_CONFIG, SECURITY, settings
from app.service.routers import router, shutdown_fraud_service

logger = logging.getLogger(__name__)

broker = KafkaBroker(
    settings.KAFKA_BROKERS,
    security=SECURITY,
    config=cast(ConfluentConfig, KAFKA_CONFIG),
    logger=logger,
)

broker.include_router(router)


class CyberStreamerApp(FastAPI):
    """Cyber Streamer Application."""

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super().__init__(*args, **kwargs)


@asynccontextmanager
async def lifespan(_app: CyberStreamerApp):
    """Handle application lifespan."""
    await broker.start()
    yield
    await broker.close()
    await shutdown_fraud_service()


app = CyberStreamerApp(
    title="CyberStreamerApp",
    description="CyberStreamerApp",
    version="0.3.0",
    contact="Stef",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    """Check application health."""
    return {"status": "healthy"}
