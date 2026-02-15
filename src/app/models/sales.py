"""Sales models module."""

import datetime

from pydantic import BaseModel, field_serializer

from app.models import SaleBaseModelLakehouse, SaleBaseEnvelopeWrapper


class Sale(BaseModel):
    """Class representing Sales."""

    start_date: datetime.datetime
    brand: str
    sub_brand: str
    campaign_name: str
    sale_amount: float
    currency: str
    mmm_model: str


class SaleLakehouse(SaleBaseModelLakehouse):
    """Class representing media channel Sale in Lakehouse."""

    @field_serializer("week")
    def serialize_dt(self, dt: datetime.datetime) -> str:
        """Serialize datetime to string."""
        return dt.strftime("%Y-%m-%d")


class SaleEnvelope(SaleBaseEnvelopeWrapper):
    """Class representing an event with a media channel payload."""

    payload: Sale
    prev_payload: Sale | None = None

    @staticmethod
    def get_current_week_monday(start_date: datetime.datetime) -> datetime.date:
        """Get the Monday of the current week."""
        return (start_date - datetime.timedelta(days=start_date.weekday())).date()

    def to_lakehouse(self, *args) -> SaleLakehouse:
        """Convert to Lakehouse model."""
        return SaleLakehouse(
            week=self.get_current_week_monday(self.payload.start_date),
            campaign_name=self.payload.campaign_name,
            brand=self.payload.brand,
            sub_brand=self.payload.sub_brand,
            cost=0.0,
            sales_amount=self.payload.sale_amount,
            currency=self.payload.currency,
            mmm_model=self.payload.mmm_model,
            media_channel="sale",
        )
