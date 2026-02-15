"""Fraud detection processor."""

import datetime
import json
import logging
import asyncio

import polars as pl

from app.llm import OllamaClient
from app.models.fraud import FraudScore

logger = logging.getLogger(__name__)

llm_client = OllamaClient()


async def process_fraud(user_id: str):
    """Process fraud detection for a user."""
    logger.info("Processing fraud for user: %s", user_id)

    # 1. Gather historical data from Bronze layer
    # Note: In a real production system, you might query a state store or a fast serving layer
    # Here we query the Delta tables directly for simplicity

    try:
        # Load recent history (last 30 days usually, but here all for demo)
        df_logins = _load_table("lakehouse/bronze/login", user_id)
        df_buys = _load_table("lakehouse/bronze/buy", user_id)
        df_scrolls = _load_table("lakehouse/bronze/scroll", user_id)
        df_orders = _load_table("lakehouse/bronze/order", user_id)

        # Prepare context for LLM
        context = {
            "user_id": user_id,
            "logins": df_logins.to_dicts() if not df_logins.is_empty() else [],
            "buys": df_buys.to_dicts() if not df_buys.is_empty() else [],
            "scrolls": df_scrolls.to_dicts() if not df_scrolls.is_empty() else [],
            "orders": df_orders.to_dicts() if not df_orders.is_empty() else [],
        }

        prompt = _build_fraud_prompt(context)

        # Call LLM
        # We run this in a thread pool to avoid blocking the async event loop
        response_json = await asyncio.to_thread(llm_client.generate, prompt)

        if response_json:
            try:
                result = json.loads(response_json)
                score = result.get("fraud_probability", 0.0)
                reason = result.get("reason", "No reason provided")

                fraud_score = FraudScore(
                    user_id=user_id,
                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                    score=score,
                    reason=reason,
                )

                # Write to Gold layer
                _write_fraud_score(fraud_score)

            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response: %s", response_json)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error processing fraud for user %s: %s", user_id, e)


def _load_table(path: str, user_id: str) -> pl.DataFrame:
    """Load data from Delta table filtered by user_id."""
    try:
        return pl.read_delta(path).filter(pl.col("user_id") == user_id)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Error loading table %s: %s", path, e)
        return pl.DataFrame()


def _write_fraud_score(score: FraudScore):
    """Write fraud score to Delta Lake."""
    # Ensure directory exists
    import os  # pylint: disable=import-outside-toplevel

    os.makedirs("lakehouse/gold/fraud_score", exist_ok=True)

    df = pl.DataFrame([score.model_dump()])
    df.write_delta(
        target="lakehouse/gold/fraud_score",
        mode="append",
        delta_write_options={"partition_by": "user_id"},
    )
    logger.info("Written fraud score: %s", score)


def _build_fraud_prompt(context: dict) -> str:
    """Build prompt for fraud detection."""
    return f"""
    Analyze the following user activity history for fraud detection.

    User Activity:
    {json.dumps(context, default=str, indent=2)}

    Task:
    Calculate the probability (0 to 1) that the recent activity is fraudulent.
    Consider:
    - Unusual login locations or devices.
    - High frequency of high-value orders.
    - Erratic scrolling behavior or lack thereof (bot-like).
    - Mismatch between user profile and activity (if available).

    Respond STRICTLY in JSON format:
    {{
        "fraud_probability": <float between 0 and 1>,
        "reason": "<brief explanation>"
    }}
    """
