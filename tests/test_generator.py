"""Tests for event generator."""

import unittest
from unittest.mock import patch, MagicMock
import json
from app.generator import EventGenerator
from app.constants import TOPIC_USER, TOPIC_LOGIN, TOPIC_BUY


class TestEventGenerator(unittest.TestCase):
    """Test EventGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        patcher = patch("app.generator.Producer")
        self.mock_producer_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_producer = MagicMock()
        self.mock_producer_cls.return_value = self.mock_producer
        self.generator = EventGenerator(bootstrap_servers="localhost:9092")

    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.generator.producer)

    def test_produce(self):
        """Test produce method."""
        topic = "test-topic"
        data = {"key": "value", "user_id": "u1"}

        self.generator.produce(topic, data)

        self.mock_producer.produce.assert_called_once()
        args, kwargs = self.mock_producer.produce.call_args
        self.assertEqual(args[0], topic)
        self.assertEqual(kwargs["key"], "u1")
        self.assertEqual(json.loads(kwargs["value"]), data)
        self.mock_producer.poll.assert_called_with(0)

    def test_produce_error(self):
        """Test produce error handling."""
        self.mock_producer.produce.side_effect = Exception("Kafka error")
        # Should not raise exception (logs error)
        self.generator.produce("topic", {"data": 1})
        self.mock_producer.produce.assert_called_once()

    def test_flush(self):
        """Test flush."""
        self.generator.flush()
        self.mock_producer.flush.assert_called_once()

    def test_generate_user(self):
        """Test generate_user."""
        topic, event = self.generator.generate_user()
        self.assertEqual(topic, TOPIC_USER)
        self.assertIn("user_id", event)
        self.assertIn("email", event)

    def test_generate_login(self):
        """Test generate_login."""
        topic, event = self.generator.generate_login(user_id="u1", is_bot=True)
        self.assertEqual(topic, TOPIC_LOGIN)
        self.assertEqual(event["user_id"], "u1")
        self.assertTrue(event["success"])

    def test_generate_buy(self):
        """Test generate_buy."""
        topic, event = self.generator.generate_buy(user_id="u1")
        self.assertEqual(topic, TOPIC_BUY)
        self.assertEqual(event["user_id"], "u1")
        self.assertIn("amount", event)

    @patch("time.sleep")
    def test_run_scenario_bot_attack(self, _):
        """Test bot attack scenario."""
        self.generator.run_scenario_bot_attack(target_user="bad_bot")

        # 15 logins + 1 buy = 16 calls
        self.assertEqual(self.mock_producer.produce.call_count, 16)
        self.mock_producer.flush.assert_called_once()

    @patch("time.sleep")
    def test_run_scenario_normal_traffic(self, _):
        """Test normal traffic scenario."""
        count = 5
        self.generator.run_scenario_normal_traffic(count=count)

        self.assertEqual(self.mock_producer.produce.call_count, count)
        self.mock_producer.flush.assert_called_once()
