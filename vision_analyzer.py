"""
Building photo analysis using OpenAI Vision API.

Extracts architectural characteristics from a facade photo:
style, era estimate, construction type, materials, floor count,
condition assessment, and notable features.
"""

import json
import logging

import requests

from src.prompts import VISION_SYSTEM_PROMPT, VISION_USER_PROMPT

logger = logging.getLogger(__name__)

API_URL = "https://api.openai.com/v1/chat/completions"


class VisionAnalyzer:
    """Analyzes building photos using multimodal LLM."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    async def analyze(self, photo_b64: str, address: str) -> dict:
        """
        Analyze a building photo and return structured visual data.

        Args:
            photo_b64: Base64-encoded JPEG image.
            address: Building address for context.

        Returns:
            Dict with keys: style, era, floors, materials, construction,
            condition, features, facade_description, tokens.
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": VISION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{photo_b64}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": VISION_USER_PROMPT.format(address=address),
                        },
                    ],
                },
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"},
        }

        try:
            resp = self.session.post(API_URL, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)

            parsed = json.loads(content)
            parsed["tokens"] = total_tokens
            return parsed

        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            logger.error("Vision analysis failed: %s", e)
            return self._fallback_result(str(e))

    @staticmethod
    def _fallback_result(error: str) -> dict:
        """Return a safe fallback when analysis fails."""
        return {
            "style": "unknown",
            "era": "unknown",
            "floors": "unknown",
            "materials": [],
            "construction": "unknown",
            "condition": "unable to assess",
            "features": [],
            "facade_description": f"Analysis failed: {error}",
            "tokens": 0,
        }
