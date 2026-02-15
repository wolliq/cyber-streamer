"""Fraud detection data models."""

import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class EventType(str, Enum):
    """Event type enum."""

    LOGIN = "login"
    BUY = "buy"
    SCROLL = "scroll"


class User(BaseModel):
    """User model."""

    user_id: str
    email: str
    phone: str
    address: str
    registration_date: datetime.datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Article(BaseModel):
    """Article model."""

    article_id: str
    name: str
    category: str
    price: float
    currency: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Order(BaseModel):
    """Order model."""

    order_id: str
    user_id: str
    article_id: str
    quantity: int
    total_price: float
    currency: str
    timestamp: datetime.datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Login(BaseModel):
    """Login event model."""

    user_id: str
    timestamp: datetime.datetime
    ip_address: str
    device_id: str
    success: bool

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Buy(BaseModel):
    """Buy event model."""

    user_id: str
    order_id: str
    timestamp: datetime.datetime
    payment_method: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Scroll(BaseModel):
    """Scroll event model."""

    user_id: str
    article_id: str
    timestamp: datetime.datetime
    percentage: float
    duration_seconds: float

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FraudScore(BaseModel):
    """Fraud score model."""

    user_id: str
    timestamp: datetime.datetime
    score: float
    reason: str

    model_config = ConfigDict(arbitrary_types_allowed=True)
