"""Ollama provider module."""

import asyncio
import json

from dataclasses import dataclass
from typing import List

import httpx
from loguru import logger
from app.constants import OLLAMA_URL, OLLAMA_MODEL


@dataclass
class FraudResult:
    """Result of fraud analysis."""

    score: float
    reason: str
    is_critical: bool


class OllamaProvider:
    """Manages interactions with local Ollama instance with concurrency control."""

    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
        concurrency_limit: int = 5,
    ):
        """Initialize OllamaProvider."""
        self.base_url = base_url
        self.model = model
        # Semaphore acts as a token bucket to limit concurrent queries
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def analyze_behavior(self, events: List[dict]) -> FraudResult:
        """Analyze a batch of events using the LLM."""
        prompt = self._build_system_prompt(events)

        try:
            # Critical: Acquire semaphore before hitting the LLM
            async with self.semaphore:
                logger.debug("Acquired semaphore for LLM inference")
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                response.raise_for_status()
                data = response.json()

            # Parse response
            response_text = data.get("response", "{}")
            try:
                parsed = json.loads(response_text)
                score = float(parsed.get("score", 0.0))
                reason = parsed.get("reason", "No reason provided")
            except (json.JSONDecodeError, ValueError):
                logger.error("Failed to parse LLM response JSON: %s", response_text)
                return FraudResult(0.0, "Response Parsing Error", False)

            return FraudResult(score=score, reason=reason, is_critical=score >= 1.0)

        except httpx.RequestError as e:
            logger.error("Ollama connection failed: %s", e)
            # Fail safe
            return FraudResult(0.0, f"Connection Error: {str(e)}", False)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Ollama inference failed: %s", e)
            return FraudResult(0.0, f"Inference Error: {str(e)}", False)

    def _build_system_prompt(self, events: List[dict]) -> str:
        return f"""
        SYSTEM: You are a Senior Fraud Analyst. Detect bot-like behavior.

        INPUT METADATA:
        timestamp, event_type, ip_address, user_agent, payload

        EVENTS ({len(events)} in window):
        {json.dumps(events, indent=2, default=str)}

        CRITERIA:
        - High frequency (bot usage)
        - Illogical sequence (buy before login, or buy immediately after login)
        - Suspicious User-Agents

        OUTPUT FORMAT (JSON ONLY):
        {{
            "score": <float 0.0-1.0>,
            "reason": "<string>"
        }}
        """

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
