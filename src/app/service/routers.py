"""Fraud detection routers."""

import logging

import polars as pl
from faststream.confluent import KafkaRouter, KafkaRoute

from app.constants import (
    TOPIC_USER,
    TOPIC_ORDER,
    TOPIC_ARTICLE,
    TOPIC_LOGIN,
    TOPIC_BUY,
    TOPIC_SCROLL,
)
from app.models.fraud import User, Order, Article, Login, Buy, Scroll
from app.processor.silver_proc import process_fraud

logger = logging.getLogger(__name__)


async def handle_user_event(event: User):
    """Handle user event."""
    logger.info("Received user event: %s", event)
    df = pl.DataFrame([event.model_dump()])
    df.write_delta(
        target="lakehouse/bronze/user",
        mode="append",
        delta_write_options={"partition_by": "registration_date"},
    )


async def handle_order_event(event: Order):
    """Handle order event."""
    logger.info("Received order event: %s", event)
    df = pl.DataFrame([event.model_dump()])
    df.write_delta(
        target="lakehouse/bronze/order",
        mode="append",
        delta_write_options={"partition_by": "timestamp"},
    )
    await process_fraud(event.user_id)


async def handle_article_event(event: Article):
    """Handle article event."""
    logger.info("Received article event: %s", event)
    df = pl.DataFrame([event.model_dump()])
    df.write_delta(
        target="lakehouse/bronze/article",
        mode="append",
        delta_write_options={"partition_by": "category"},
    )


async def handle_login_event(event: Login):
    """Handle login event."""
    logger.info("Received login event: %s", event)
    df = pl.DataFrame([event.model_dump()])
    df.write_delta(
        target="lakehouse/bronze/login",
        mode="append",
        delta_write_options={"partition_by": "timestamp"},
    )
    await process_fraud(event.user_id)


async def handle_buy_event(event: Buy):
    """Handle buy event."""
    logger.info("Received buy event: %s", event)
    df = pl.DataFrame([event.model_dump()])
    df.write_delta(
        target="lakehouse/bronze/buy",
        mode="append",
        delta_write_options={"partition_by": "timestamp"},
    )
    await process_fraud(event.user_id)


async def handle_scroll_event(event: Scroll):
    """Handle scroll event."""
    logger.info("Received scroll event: %s", event)
    df = pl.DataFrame([event.model_dump()])
    df.write_delta(
        target="lakehouse/bronze/scroll",
        mode="append",
        delta_write_options={"partition_by": "timestamp"},
    )
    await process_fraud(event.user_id)


router = KafkaRouter(
    handlers=(
        KafkaRoute(handle_user_event, TOPIC_USER),
        KafkaRoute(handle_order_event, TOPIC_ORDER),
        KafkaRoute(handle_article_event, TOPIC_ARTICLE),
        KafkaRoute(handle_login_event, TOPIC_LOGIN),
        KafkaRoute(handle_buy_event, TOPIC_BUY),
        KafkaRoute(handle_scroll_event, TOPIC_SCROLL),
    )
)
