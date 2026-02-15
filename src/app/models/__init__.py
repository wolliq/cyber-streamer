"""Models module."""

from abc import abstractmethod
import datetime

from pydantic import BaseModel

####################################################
# Classes for Lakehouse serde
####################################################


class MediaBaseModelLakehouse(BaseModel):
    """Class base for lakehouse storage."""

    week: datetime.date
    campaign_name: str
    brand: str
    sub_brand: str
    media_channel: str

    class Config:
        """Configuration for Pydantic model."""

        arbitrary_types_allowed = True


class SaleBaseModelLakehouse(BaseModel):
    """Class base for sales in Lakehouse."""

    week: datetime.date
    campaign_name: str
    brand: str
    sub_brand: str
    media_channel: str
    cost: float
    sales_amount: float
    currency: str
    mmm_model: str

    class Config:
        """Configuration for Pydantic model."""

        arbitrary_types_allowed = True


####################################################
# Classes for Kafka serde
####################################################


class MediaBaseEnvelopeWrapper(BaseModel):
    """Class base BaseEnvelopeWrapper."""

    event_uuid: str
    event_ts: int
    event_type: str
    occurred_ts: int | None = None
    channel: str | None = "radio"
    request_origin: str | None = "data-api"
    payload: BaseModel
    prev_payload: BaseModel | None = None

    @staticmethod
    def flatten(data: dict) -> dict:
        """Recursively flatten the dictionary and return a flat dict."""
        flat_dict = {}

        def _flatten(d, parent_key=""):
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):  # If the value is another dictionary
                    _flatten(v, new_key)
                elif isinstance(
                    v, list
                ):  # If the value is a list (this could also be handled)
                    for idx, item in enumerate(v):
                        _flatten(item, f"{new_key}[{idx}]")
                else:
                    flat_dict[new_key] = v

        _flatten(data)
        return flat_dict

    class Config:
        """Configuration for Pydantic model."""

        arbitrary_types_allowed = True

    @staticmethod
    @abstractmethod
    def get_current_week_monday(start_date: datetime.datetime) -> datetime.date:
        """Get the Monday of the current week."""

    @abstractmethod
    def to_lakehouse(self, *args) -> MediaBaseModelLakehouse:
        """Convert to Lakehouse model."""


class SaleBaseEnvelopeWrapper(BaseModel):
    """Class base BaseEnvelopeWrapper."""

    event_uuid: str
    event_ts: int
    event_type: str
    occurred_ts: int | None = None
    channel: str | None = "sale"
    request_origin: str | None = "data-api"
    payload: BaseModel
    prev_payload: BaseModel | None = None

    class Config:
        """Configuration for Pydantic model."""

        arbitrary_types_allowed = True

    @staticmethod
    def flatten(data: dict) -> dict:
        """Recursively flatten the dictionary and return a flat dict."""
        flat_dict = {}

        def _flatten(d, parent_key=""):
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):  # If the value is another dictionary
                    _flatten(v, new_key)
                elif isinstance(
                    v, list
                ):  # If the value is a list (this could also be handled)
                    for idx, item in enumerate(v):
                        _flatten(item, f"{new_key}[{idx}]")
                else:
                    flat_dict[new_key] = v

        _flatten(data)
        return flat_dict

    @staticmethod
    @abstractmethod
    def get_current_week_monday(start_date: datetime.datetime) -> datetime.date:
        """Get the Monday of the current week."""

    @abstractmethod
    def to_lakehouse(self, *args) -> SaleBaseModelLakehouse:
        """Convert to Lakehouse model."""
