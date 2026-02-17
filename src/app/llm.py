"""LLM Client for Ollama."""

import json

from typing import Optional

import requests
from loguru import logger

from app.constants import OLLAMA_URL, OLLAMA_MODEL


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = OLLAMA_URL, model: str = OLLAMA_MODEL):
        """Initialize Ollama client."""
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str) -> Optional[str]:
        """Generate response from Ollama."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result.get("response")

        except requests.exceptions.RequestException as e:
            logger.error("Error calling Ollama API: %s", e)
            return None
        except json.JSONDecodeError as e:
            logger.error("Error decoding Ollama response: %s", e)
            return None
