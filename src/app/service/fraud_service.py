"""Fraud detection service."""

import json

import time
import datetime

import redis.asyncio as redis
from loguru import logger

from app.constants import settings
from app.models.fraud import FraudScore
from app.processor.silver_proc import _write_fraud_score
from app.service.llm_provider import LLMProvider, FraudResult


class FraudService:
    """Orchestrates the Hot Path (Redis) and Intelligence (LLM)."""

    def __init__(self, redis_url: str | None = None):
        """Initialize FraudService."""
        self.redis = redis.from_url(
            redis_url or settings.REDIS_URL, decode_responses=True
        )
        self.llm = LLMProvider()
        self.window_seconds = 120  # 2 minutes
        self.threshold_count = 10

    async def process_event(self, user_id: str, event: dict):
        """Process an event for fraud detection."""
        # Ensure event is serializable
        try:
            event_str = json.dumps(event, default=str)
        except (TypeError, ValueError) as e:
            logger.error("Failed to serialize event for Redis: %s", e)
            return

        now_ts = time.time()
        key = f"user_events:{user_id}"
        alert_lock_key = f"last_alert:{user_id}"

        try:
            async with self.redis.pipeline() as pipe:
                # 1. Add event to ZSET (Score = Timestamp)
                await pipe.zadd(key, {event_str: now_ts})
                # 2. Remove old events (Sliding Window)
                await pipe.zremrangebyscore(key, "-inf", now_ts - self.window_seconds)
                # 3. Count remaining events
                await pipe.zcard(key)
                # 4. Refresh TTL on key
                await pipe.expire(key, self.window_seconds + 60)

                results = await pipe.execute()
        except redis.RedisError as e:
            logger.error("Redis operation failed: %s", e)
            return

        current_count = results[2]

        if current_count >= self.threshold_count:
            # Check if we recently alerted
            if await self.redis.get(alert_lock_key):
                logger.info(
                    "Skipping LLM: Alert already sent for %s in recent window.", user_id
                )
                return

            # Get events for analysis
            events_in_window = await self.redis.zrange(key, 0, -1)
            # Parse back to dicts
            parsed_events = [json.loads(e) for e in events_in_window]

            # Trigger Intelligence
            logger.warning(
                "Threshold breached (%d) for %s. triggering LLM.",
                current_count,
                user_id,
            )
            for parsed_event in parsed_events:
                logger.info(
                    "Event sent to LLM: {}", json.dumps(parsed_event, default=str)
                )

            result = await self.llm.analyze_behavior(parsed_events)

            if result.score >= 0.6:
                await self._handle_fraud_detection(user_id, result)
                # Set alert lock to avoid spamming for the duration of this window
                await self.redis.setex(alert_lock_key, self.window_seconds, "1")

    async def _handle_fraud_detection(self, user_id: str, result: FraudResult):
        """Handle detected fraud."""
        severity = "CRITICAL" if result.is_critical else "SUSPICIOUS"
        logger.warning(
            f"[{severity}] Fraud Detected for {user_id}: Score {result.score} - {result.reason}",
        )

        # Create FraudScore object
        fraud_score = FraudScore(
            user_id=user_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            score=result.score,
            reason=result.reason,
        )

        # Write to Gold layer (using existing processor function for now)
        _write_fraud_score(fraud_score)

    async def close(self):
        """Close resources."""
        await self.redis.close()
        await self.llm.close()
