"""Tests for silver processor."""

import unittest
from unittest.mock import patch, MagicMock
from app.processor.silver_proc import process_fraud


class TestSilverProc(unittest.IsolatedAsyncioTestCase):
    """Test silver processor."""

    @patch("app.processor.silver_proc.llm_client")
    @patch("app.processor.silver_proc.pl.read_delta")
    @patch("app.processor.silver_proc._write_fraud_score")
    async def test_process_fraud(self, mock_write, mock_read_delta, mock_llm_client):
        """Test process_fraud."""
        # Mock Delta Tables
        mock_df = MagicMock()
        mock_df.filter.return_value = mock_df
        mock_df.is_empty.return_value = False
        mock_df.to_dicts.return_value = [{"data": 1}]
        mock_read_delta.return_value = mock_df

        # Mock LLM response
        mock_llm_client.generate.return_value = (
            '{"fraud_probability": 0.8, "reason": "suspicious"}'
        )

        user_id = "u1"
        await process_fraud(user_id)

        # Verify calls
        self.assertEqual(mock_read_delta.call_count, 4)  # 4 tables
        mock_llm_client.generate.assert_called_once()
        mock_write.assert_called_once()

        # Verify fraud score content
        args, _ = mock_write.call_args
        fraud_score = args[0]
        self.assertEqual(fraud_score.user_id, "u1")
        self.assertEqual(fraud_score.score, 0.8)

    @patch("app.processor.silver_proc.llm_client")
    @patch("app.processor.silver_proc.pl.read_delta")
    @patch("app.processor.silver_proc._write_fraud_score")
    async def test_process_fraud_llm_error(
        self, mock_write, mock_read_delta, mock_llm_client
    ):
        """Test process_fraud with LLM error."""
        # Mock Delta Tables
        mock_df = MagicMock()
        mock_df.filter.return_value = mock_df
        mock_df.is_empty.return_value = True
        mock_read_delta.return_value = mock_df

        # Mock LLM error response (e.g. invalid JSON)
        mock_llm_client.generate.return_value = "invalid json"

        await process_fraud("u1")

        mock_write.assert_not_called()
