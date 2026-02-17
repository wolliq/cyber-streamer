"""Tests for Ollama provider."""

import unittest
from unittest.mock import MagicMock, AsyncMock
import httpx
from app.service.ollama_provider import OllamaProvider, FraudResult


class TestOllamaProvider(unittest.IsolatedAsyncioTestCase):
    """Test OllamaProvider."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = OllamaProvider(base_url="http://test:11434", model="test-model")

    async def test_analyze_behavior_success(self):
        """Test successful analysis."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"score": 0.9, "reason": "bad"}'
        }

        self.provider.client.post = AsyncMock(return_value=mock_response)

        events = [{"event": 1}]
        result = await self.provider.analyze_behavior(events)

        self.assertIsInstance(result, FraudResult)
        self.assertEqual(result.score, 0.9)
        self.assertEqual(result.reason, "bad")
        self.assertFalse(result.is_critical)  # 0.9 < 1.0

    async def test_analyze_behavior_critical(self):
        """Test critical fraud."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"score": 1.0, "reason": "very bad"}'
        }

        self.provider.client.post = AsyncMock(return_value=mock_response)

        result = await self.provider.analyze_behavior([{}])
        self.assertTrue(result.is_critical)

    async def test_analyze_behavior_http_error(self):
        """Test HTTP error."""
        self.provider.client.post = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        result = await self.provider.analyze_behavior([{}])
        self.assertEqual(result.score, 0.0)
        self.assertIn("Connection Error", result.reason)

    async def test_analyze_behavior_json_error(self):
        """Test JSON parse error from LLM."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "not json"}

        self.provider.client.post = AsyncMock(return_value=mock_response)

        result = await self.provider.analyze_behavior([{}])
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.reason, "Response Parsing Error")

    async def test_close(self):
        """Test close."""
        self.provider.client.aclose = AsyncMock()
        await self.provider.close()
        self.provider.client.aclose.assert_called_once()
