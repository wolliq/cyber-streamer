"""Tests for LLM client."""

import unittest
from unittest.mock import patch, MagicMock
import requests
from app.llm import OllamaClient


class TestOllamaClient(unittest.TestCase):
    """Test OllamaClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = OllamaClient(base_url="http://test:11434", model="test-model")

    @patch("app.llm.requests.post")
    def test_generate_success(self, mock_post):
        """Test successful generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": '{"score": 0.9}'}
        mock_post.return_value = mock_response

        response = self.client.generate("test prompt")

        self.assertEqual(response, '{"score": 0.9}')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://test:11434/api/generate")
        self.assertEqual(kwargs["json"]["model"], "test-model")

    @patch("app.llm.requests.post")
    def test_generate_request_error(self, mock_post):
        """Test request error."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        response = self.client.generate("test prompt")
        self.assertIsNone(response)

    @patch("app.llm.requests.post")
    def test_generate_json_error(self, mock_post):
        """Test JSON decode error."""
        mock_response = MagicMock()
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "msg", "doc", 0
        )
        mock_post.return_value = (
            mock_response  # raise_for_status not called on mock unless configured
        )

        # Ideally raise_for_status should be called, let's mock it to pass or fail
        # In code: response.raise_for_status() is called before json()

        response = self.client.generate("test prompt")
        # In current implementation, if json() fails it returns None.
        # But wait, requests.exceptions.JSONDecodeError is not
        # standard json.JSONDecodeError in old requests?
        # app.llm imports json and catches json.JSONDecodeError

        self.assertIsNone(response)
