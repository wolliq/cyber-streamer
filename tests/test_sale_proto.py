"""Test Sale Proto module."""

# pylint: disable=no-member
from tests import sale_pb2


def main():
    """Test serialization and deserialization of SaleEnvelope."""
    # Create a SalePayload instance
    sale_payload = sale_pb2.SalePayload(
        start_date="2024-06-15T08:00:00Z",  # ISO 8601 string
        brand="MediaOne",
        sub_brand="FM 101",
        campaign_name="Summer Vibes",
        sale_amount=250.00,
        currency="EUR",
        mmm_model="MMM-2024",
    )

    # Create a SaleEnvelope instance
    sale_event = sale_pb2.SaleEnvelope(
        event_uuid="12345-abcde",
        event_ts=1738511979000,
        event_type="typeA",
        occurred_ts=1738511979000,
        channel="sale",
        request_origin="data-api",
        payload=sale_payload,
        prev_payload=None,
    )

    # Serialize to binary
    serialized_data = sale_event.SerializeToString()

    # Deserialize from binary
    new_event = sale_pb2.SaleEnvelope()
    new_event.ParseFromString(serialized_data)

    # Assertions
    assert new_event.event_uuid == "12345-abcde"
    assert new_event.event_ts == 1738511979000
    assert new_event.event_type == "typeA"
    assert new_event.channel == "sale"
    assert new_event.request_origin == "data-api"

    # Assert payload data
    assert new_event.payload.start_date == "2024-06-15T08:00:00Z"
    assert new_event.payload.brand == "MediaOne"
    assert new_event.payload.sub_brand == "FM 101"
    assert new_event.payload.campaign_name == "Summer Vibes"
    assert new_event.payload.sale_amount == 250.00
    assert new_event.payload.currency == "EUR"
    assert new_event.payload.mmm_model == "MMM-2024"

    # Assert prev_payload is not set
    assert not new_event.HasField("prev_payload")
    return True


def test_sale_proto():
    """Test the main function."""
    assert main()
