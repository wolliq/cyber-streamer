import logging
import datetime
import time
from tests import media_tv_pb2

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def create_media_tv_event(
    brand,
    sub_brand,
    campaign_name,
    start_date_iso,
    cost,
    currency,
    event_type,
    channel,
    request_origin,
    prev_brand=None,
):
    """Creates a MediaRadioEnvelope object."""

    payload = media_tv_pb2.MediaTvPayload()
    payload.brand = brand
    payload.sub_brand = sub_brand
    payload.campaign_name = campaign_name
    payload.start_date = start_date_iso
    payload.cost = cost
    payload.currency = currency

    envelope = media_tv_pb2.MediaTvEnvelope()
    envelope.event_uuid = "your-unique-uuid"  # In a real application, generate a UUID
    envelope.event_ts = int(time.time())  # Current timestamp (seconds since epoch)

    envelope.event_type = event_type
    envelope.occurred_ts = int(time.time())  # Current timestamp (seconds since epoch)
    envelope.channel = channel
    envelope.request_origin = request_origin
    envelope.payload.CopyFrom(payload)

    if prev_brand:
        prev_payload = media_tv_pb2.MediaTvPayload()
        prev_payload.brand = prev_brand
        envelope.prev_payload.CopyFrom(prev_payload)

    return envelope


def main():
    """Demonstrates creating, serializing, and deserializing a MediaTvEnvelope."""

    # Example usage:
    start_date_iso = (
        datetime.datetime(2024, 11, 1, 10, 0, 0).isoformat() + "Z"
    )  # Example ISO 8601 date
    event = create_media_tv_event(
        brand="TvBrandA",
        sub_brand="TvSubBrand1",
        campaign_name="SummerCampaign",
        start_date_iso=start_date_iso,
        cost=1500.50,
        currency="EUR",
        event_type="CampaignStart",
        channel="Tv",
        request_origin="MarketingSystem",
        prev_brand="OldBrandX",  # Example of previous brand
    )

    # Serialize to a byte string
    serialized_event = event.SerializeToString()
    logger.info("Serialized event:", serialized_event)

    # Deserialize from the byte string
    deserialized_event = media_tv_pb2.MediaTvEnvelope()
    deserialized_event.ParseFromString(serialized_event)

    # Print the deserialized data
    logger.info("\nDeserialized event:")
    logger.info("Brand:", deserialized_event.payload.brand)
    logger.info(
        "Previous Brand (if set):",
        (
            deserialized_event.prev_payload.brand
            if deserialized_event.HasField("prev_payload")
            else "Not set"
        ),
    )
    logger.info("Event Timestamp:", deserialized_event.event_ts)
    logger.info("Start Date:", deserialized_event.payload.start_date)
    logger.info("Cost:", deserialized_event.payload.cost)
    logger.info("Currency:", deserialized_event.payload.currency)
    logger.info("Event Type:", deserialized_event.event_type)

    # Example without previous brand
    event2 = create_media_tv_event(
        brand="TvBrandB",
        sub_brand="TvSubBrand2",
        campaign_name="WinterCampaign",
        start_date_iso=start_date_iso,
        cost=2000.00,
        currency="USD",
        event_type="CampaignStart",
        channel="Tv",
        request_origin="MarketingSystem",
    )
    serialized_event2 = event2.SerializeToString()
    deserialized_event2 = media_tv_pb2.MediaTvEnvelope()
    deserialized_event2.ParseFromString(serialized_event2)
    logger.info("\nDeserialized event 2:")
    logger.info("Brand:", deserialized_event2.payload.brand)
    logger.info(
        "Previous Brand (if set):",
        (
            deserialized_event2.prev_payload.brand
            if deserialized_event2.HasField("prev_payload")
            else "Not set"
        ),
    )  # Correct way to access optional fields
    logger.info("Cost:", deserialized_event2.payload.cost)

    return True


def test_media_tv_proto():
    assert main()
