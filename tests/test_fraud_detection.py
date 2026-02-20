"""Tests for fraud detection."""

import datetime
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import logging

from app.models.fraud import User, Order
from app.service.fraud_service import FraudService
from app.service.llm_provider import FraudResult


class TestFraudModels(unittest.TestCase):
    """Test fraud data models."""

    def test_user_model(self):
        """Test User model."""
        user = User(
            user_id="u1",
            email="test@example.com",
            phone="+1234567890",
            address="123 Main St",
            registration_date=datetime.datetime.now(),
        )
        self.assertEqual(user.user_id, "u1")

    def test_order_model(self):
        """Test Order model."""
        order = Order(
            order_id="o1",
            user_id="u1",
            article_id="a1",
            quantity=1,
            total_price=10.0,
            currency="USD",
            timestamp=datetime.datetime.now(),
        )
        self.assertEqual(order.user_id, "u1")
        self.assertEqual(order.total_price, 10.0)


class TestFraudService(unittest.IsolatedAsyncioTestCase):
    """Test FraudService logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.logger = logging.getLogger("app.service.fraud_service")

    @patch("app.service.fraud_service.redis.from_url")
    @patch("app.service.fraud_service.LLMProvider")
    @patch("app.service.fraud_service._write_fraud_score")
    async def test_process_event_threshold_breach(
        self, mock_write, mock_llm_cls, mock_redis_from_url
    ):
        """Test processing event resulting in fraud check."""
        # 1. Mock Redis
        mock_redis = MagicMock()  # Client methods like pipeline() are sync
        mock_redis_from_url.return_value = mock_redis

        # Pipeline mocks
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.__aenter__.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [
            1,
            1,
            10,
            True,
        ]  # ZADD, REM, CARD=10, EXPIRE

        # Redis Get (Alert Lock) and ZRange need to be async
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.zrange = AsyncMock(
            return_value=['{"event_type": "login", "timestamp": 123}']
        )
        mock_redis.setex = AsyncMock()

        # 2. Mock LLM
        mock_llm_instance = mock_llm_cls.return_value
        mock_llm_instance.analyze_behavior = AsyncMock(
            return_value=FraudResult(
                score=0.85, reason="Suspicious activity", is_critical=False
            )
        )

        # 3. Instantiate Service
        service = FraudService()

        # 4. Call process_event
        event = {"event_type": "login", "user_id": self.user_id, "timestamp": 123}
        await service.process_event(self.user_id, event)

        # 5. Assertions
        # Redis pipeline called
        mock_pipeline.zadd.assert_called()
        mock_pipeline.zcard.assert_called()

        # Threshold met (10), so ZRange called
        mock_redis.zrange.assert_called()

        # LLM called
        mock_llm_instance.analyze_behavior.assert_called()

        # Write score called
        mock_write.assert_called_once()

        # Alert lock set
        mock_redis.setex.assert_called_with(f"last_alert:{self.user_id}", 120, "1")

    @patch("app.service.fraud_service.redis.from_url")
    @patch("app.service.fraud_service.LLMProvider")
    @patch("app.service.fraud_service._write_fraud_score")
    async def test_process_event_no_threshold(
        self, mock_write, mock_llm_cls, mock_redis_from_url
    ):
        """Test processing event below threshold."""
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis

        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.__aenter__.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [1, 1, 5, True]  # CARD=5

        # Mock other asyncio methods on redis client just in case
        mock_redis.zadd = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard = AsyncMock()
        mock_redis.expire = AsyncMock()

        service = FraudService()
        event = {"event_type": "login", "user_id": self.user_id}
        await service.process_event(self.user_id, event)

        # LLM NOT called
        mock_llm_cls.return_value.analyze_behavior.assert_not_called()

        # Write score NOT called
        mock_write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
