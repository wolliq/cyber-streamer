"""Routers module."""

import datetime
import logging

import polars as pl
from faststream.confluent import KafkaRouter, KafkaRoute

from app.constants import TOPIC_MEDIA_RADIO, TOPIC_MEDIA_TV, TOPIC_SALE
from app.models.media_channel_radio import MediaChannelRadioEnvelope
from app.models.media_channel_tv import MediaChannelTvEnvelope
from app.models.sales import SaleEnvelope

logger = logging.getLogger(__name__)


async def handle_media_radio_event(event: MediaChannelRadioEnvelope):
    """Handle media radio event."""
    logger.info(event)
    data = event.flatten(event.model_dump())
    df = pl.DataFrame(data)
    df = df.with_columns(pl.all().fill_null("NULL"))

    df = df.with_columns(
        occurred_date=pl.from_epoch(
            pl.col("occurred_ts").cast(pl.Int64), time_unit="ms"
        ).cast(pl.Date)
    ).with_columns(
        monday_of_week=pl.col("occurred_date").map_elements(
            lambda dt: dt - datetime.timedelta(days=dt.weekday()), return_dtype=pl.Date
        )
    )

    logger.info(df.head())

    table_path = "lakehouse/bronze/media_radio"

    delta_write_options = {"partition_by": "monday_of_week"}
    df.write_delta(
        target=table_path, mode="append", delta_write_options=delta_write_options
    )

    logger.info("Delta lake written: media_radio table")


router_media_radio = KafkaRouter(
    handlers=(
        KafkaRoute(
            handle_media_radio_event,
            TOPIC_MEDIA_RADIO,
        ),
    )
)


async def handle_media_tv_event(event: MediaChannelTvEnvelope):
    """Handle media tv event."""
    logger.info(event)
    data = event.flatten(event.model_dump())
    df = pl.DataFrame(data)
    df = df.with_columns(pl.all().fill_null("NULL"))

    df = df.with_columns(
        occurred_date=pl.from_epoch(
            pl.col("occurred_ts").cast(pl.Int64), time_unit="ms"
        ).cast(pl.Date)
    ).with_columns(
        monday_of_week=pl.col("occurred_date").map_elements(
            lambda dt: dt - datetime.timedelta(days=dt.weekday()), return_dtype=pl.Date
        )
    )

    logger.info(df.head())
    table_path = "lakehouse/bronze/media_tv"
    delta_write_options = {"partition_by": "monday_of_week"}
    df.write_delta(
        target=table_path, mode="append", delta_write_options=delta_write_options
    )

    logger.info("Delta lake written: media_tv table")


router_media_tv = KafkaRouter(
    handlers=(
        KafkaRoute(
            handle_media_tv_event,
            TOPIC_MEDIA_TV,
        ),
    )
)


async def handle_sale_event(event: SaleEnvelope):
    """Handle sale event."""
    logger.info(event)
    data = event.flatten(event.model_dump())
    df = pl.DataFrame(data)
    df = df.with_columns(pl.all().fill_null("NULL"))

    df = df.with_columns(
        occurred_date=pl.from_epoch(
            pl.col("occurred_ts").cast(pl.Int64), time_unit="ms"
        ).cast(pl.Date)
    ).with_columns(
        monday_of_week=pl.col("occurred_date").map_elements(
            lambda dt: dt - datetime.timedelta(days=dt.weekday()), return_dtype=pl.Date
        )
    )

    logger.info(df.head())
    table_path = "lakehouse/bronze/sale"

    delta_write_options = {"partition_by": "monday_of_week"}
    df.write_delta(
        target=table_path, mode="append", delta_write_options=delta_write_options
    )
    logger.info("Delta lake written: sale table")


router_sale = KafkaRouter(
    handlers=(
        KafkaRoute(
            handle_sale_event,
            TOPIC_SALE,
        ),
    )
)
