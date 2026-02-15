import datetime

from pydantic import BaseModel, field_serializer

from app.models import MediaBaseEnvelopeWrapper, MediaBaseModelLakehouse


class MediaChannelTv(BaseModel):
    """
    Class representing media channel Radio
    """

    brand: str
    sub_brand: str
    campaign_name: str
    start_date: datetime.datetime
    media_channel: str = "tv"
    cost: float
    currency: str


class MediaChannelTvLakehouse(MediaBaseModelLakehouse):
    """
    Class representing media channel Radio stored in Lakehouse
    """

    @field_serializer("week")
    def serialize_dt(self, dt: datetime.datetime) -> str:
        return dt.strftime("%Y-%m-%d")


class MediaChannelTvEnvelope(MediaBaseEnvelopeWrapper):
    """
    Class representing an event with a media channel payload
    """

    payload: MediaChannelTv
    prev_payload: MediaChannelTv | None = None

    @staticmethod
    def get_current_week_monday(start_date: datetime.datetime) -> datetime.date:
        return (start_date - datetime.timedelta(days=start_date.weekday())).date()

    def to_lakehouse(self, *args) -> MediaChannelTvLakehouse:
        return MediaChannelTvLakehouse(
            week=self.get_current_week_monday(self.payload.start_date),
            campaign_name=self.payload.campaign_name,
            brand=self.payload.brand,
            sub_brand=self.payload.sub_brand,
            media_channel=self.payload.media_channel,
        )
