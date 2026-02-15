import datetime

from pydantic import BaseModel, field_serializer

from app.models import MediaBaseEnvelopeWrapper, MediaBaseModelLakehouse


class MediaChannelRadio(BaseModel):
    """
    Class representing media channel Radio
    """

    brand: str
    sub_brand: str
    campaign_name: str
    start_date: datetime.datetime
    media_channel: str = "radio"
    cost: float
    currency: str


class MediaChannelRadioLakehouse(MediaBaseModelLakehouse):
    """
    Class representing media channel Radio stored in Lakehouse
    """

    @field_serializer("week")
    def serialize_dt(self, dt: datetime.datetime) -> str:
        return dt.strftime("%Y-%m-%d")


class MediaChannelRadioEnvelope(MediaBaseEnvelopeWrapper):
    """
    Class representing an event with a media channel payload
    """

    payload: MediaChannelRadio
    prev_payload: MediaChannelRadio | None = None

    @staticmethod
    def get_current_week_monday(start_date: datetime.datetime) -> datetime.date:
        return (start_date - datetime.timedelta(days=start_date.weekday())).date()

    def to_lakehouse(self, *args) -> MediaChannelRadioLakehouse:
        return MediaChannelRadioLakehouse(
            week=self.get_current_week_monday(self.payload.start_date),
            campaign_name=self.payload.campaign_name,
            brand=self.payload.brand,
            sub_brand=self.payload.sub_brand,
            media_channel=self.payload.media_channel,
        )
