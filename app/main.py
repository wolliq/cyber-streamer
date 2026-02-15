import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.confluent import KafkaBroker
from faststream.confluent.config import ConfluentConfig  # type: ignore # pylint: disable=import-error,no-name-in-module

from app.constants import KAFKA_CONFIG, KAFKA_BROKERS, SECURITY
from app.service.routers import router_media_radio, router_media_tv, router_sale


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

broker.include_routers(router_media_radio, router_media_tv, router_sale)


# TODO accelerate via batching
# BATCH PROCESSING
#
# @broker.subscriber(TOPIC_RADIO, batch=True)  # topic name
# async def handle_msg(payloads: List[MediaBaseEnvelopeWrapper], message: KafkaMessage):
#     for radio_message, raw_message in zip(payloads, list(message.raw_message)):
#         logging.INFO(radio_message)
#         process_content(radio_message)
#


class FKLStreamerApp(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@asynccontextmanager
async def lifespan(_app: FKLStreamerApp):
    await broker.start()
    yield
    await broker.close()


app = FKLStreamerApp(
    title="FKLStreamerApp",
    description="FKLStreamerApp",
    version="0.3.0",
    contact="Stef",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
