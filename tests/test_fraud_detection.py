"""Tests for fraud detection."""

import datetime
import unittest
from unittest.mock import patch
import logging

import polars as pl

from app.models.fraud import User, Order, FraudScore
from app.processor.silver_proc import process_fraud, _build_fraud_prompt


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


class TestFraudProcessor(unittest.IsolatedAsyncioTestCase):
    """Test fraud processor."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.logger = logging.getLogger("app.processor.silver_proc")

    def test_build_prompt(self):
        """Test prompt building."""
        context = {
            "user_id": self.user_id,
            "logins": [{"timestamp": "2023-01-01", "success": True}],
            "buys": [],
            "scrolls": [],
            "orders": [],
        }
        prompt = _build_fraud_prompt(context)
        self.assertIn(self.user_id, prompt)
        self.assertIn("logins", prompt)

    @patch("app.processor.silver_proc.llm_client")
    @patch("app.processor.silver_proc._load_table")
    @patch("app.processor.silver_proc._write_fraud_score")
    async def test_process_fraud(self, mock_write, mock_load, mock_llm):
        """Test process_fraud function."""
        # Mock Delta Lake data
        mock_load.return_value = pl.DataFrame()

        # Mock LLM response
        mock_llm.generate.return_value = (
            '{"fraud_probability": 0.85, "reason": "Suspicious login location"}'
        )

        # Run processor
        await process_fraud(self.user_id)

        # Verify LLM was called
        mock_llm.generate.assert_called_once()

        # Verify score was written
        mock_write.assert_called_once()
        args, _ = mock_write.call_args
        score = args[0]
        self.assertIsInstance(score, FraudScore)
        self.assertEqual(score.user_id, self.user_id)
        self.assertEqual(score.score, 0.85)

    @patch("app.processor.silver_proc.llm_client")
    @patch("app.processor.silver_proc._load_table")
    @patch("app.processor.silver_proc._write_fraud_score")
    async def test_process_fraud_invalid_json(self, mock_write, mock_load, mock_llm):
        """Test process_fraud with invalid LLM response."""
        mock_load.return_value = pl.DataFrame()
        mock_llm.generate.return_value = "Not JSON"

        await process_fraud(self.user_id)

        mock_write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
