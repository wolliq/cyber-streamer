"""Marketing Mix Modelling models module."""

import datetime

from pydantic import BaseModel, field_serializer


class MarketingMixModelling(BaseModel):
    """Class representing MarketingMixModelling.

    Field Name Description Data Type Standardized Format
    week Start date of the week (aligned to Mondays) DATE "%Y-%m-%dT%H:%M:%SZ"
    campaignName Name of the campaign STRING Trimmed, Uppercase
    brand Main brand associated with the campaign STRING Trimmed, Uppercase
    subBrand Sub-brand under the main brand (if applicable) STRING Trimmed, Uppercase
    mediaChannel Type of media source (TV, Radio, Meta, etc.) STRING Predefined Categories
    cost Net investment or cost for media campaigns FLOAT Rounded to 2 decimals
    salesAmount Total sales revenue (applicable to sales data) FLOAT Rounded to 2 decimals
    currency Currency for sales data STRING Standardized codes (ISO)
    mmmModel Model categorization (applicable to campaigns) STRING Trimmed, Uppercase
    """

    week: datetime.datetime
    campaign_name: str
    brand: str
    sub_brand: str
    media_channel: str
    cost: float
    sales_amount: float
    currency: str
    mmm_model: str

    @field_serializer("week")
    def serialize_dt(self, dt: datetime.datetime):
        """Serialize datetime to string."""
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
