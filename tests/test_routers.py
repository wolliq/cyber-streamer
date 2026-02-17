"""Tests for routers."""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from app.models.fraud import User, Login, Buy
from app.service.routers import (
    handle_user_event,
    handle_login_event,
    handle_buy_event,
)


class TestRouters(unittest.IsolatedAsyncioTestCase):
    """Test router handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_data = {
            "user_id": "u1",
            "email": "test@example.com",
            "phone": "+1234567890",
            "address": "123 Main St",
            "registration_date": "2023-01-01T00:00:00",
        }
        self.order_data = {
            "order_id": "o1",
            "user_id": "u1",
            "article_id": "a1",
            "quantity": 1,
            "total_price": 10.0,
            "currency": "USD",
            "timestamp": "2023-01-01T00:00:00",
        }
        # Add other necessary data fixtures

    @patch("app.service.routers.pl.DataFrame")
    @patch("app.service.routers.fraud_service")
    async def test_handle_user_event(self, mock_fraud_service, mock_df_cls):
        """Test handle_user_event."""
        mock_df = MagicMock()
        mock_df_cls.return_value = mock_df

        event = User(**self.user_data)
        await handle_user_event(event)

        # Check DataFrame creation and write
        mock_df_cls.assert_called_once()
        mock_df.write_delta.assert_called_once()

        # Ensure fraud service is NOT called
        mock_fraud_service.process_event.assert_not_called()

    @patch("app.service.routers.pl.DataFrame")
    @patch("app.service.routers.fraud_service")
    async def test_handle_login_event(self, mock_fraud_service, mock_df_cls):
        """Test handle_login_event."""
        mock_df = MagicMock()
        mock_df_cls.return_value = mock_df
        # Ensure process_event is awaitable
        mock_fraud_service.process_event = AsyncMock()

        event = Login(
            user_id="u1",
            timestamp="2023-01-01T00:00:00",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            device_id="d1",
            success=True,
        )
        await handle_login_event(event)

        # Check DataFrame creation and write
        mock_df.write_delta.assert_called_once()

        # Ensure fraud service IS called
        mock_fraud_service.process_event.assert_called_once_with(
            event.user_id, event.model_dump()
        )

    @patch("app.service.routers.pl.DataFrame")
    @patch("app.service.routers.fraud_service")
    async def test_handle_buy_event(self, mock_fraud_service, mock_df_cls):
        """Test handle_buy_event."""
        mock_df = MagicMock()
        mock_df_cls.return_value = mock_df
        # Ensure process_event is awaitable
        mock_fraud_service.process_event = AsyncMock()

        event = Buy(
            user_id="u1",
            article_id="a1",
            quantity=1,
            price=10.0,
            currency="USD",
            timestamp="2023-01-01T00:00:00",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            order_id="o1",
            payment_method="credit_card",
        )
        await handle_buy_event(event)

        mock_df.write_delta.assert_called_once()
        mock_fraud_service.process_event.assert_called_once_with(
            event.user_id, event.model_dump()
        )


if __name__ == "__main__":
    unittest.main()
