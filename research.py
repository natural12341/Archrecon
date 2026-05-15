"""
Historical research module.

Uses LLM with web search context to gather information about
a building's history, architect, heritage status, and context.
Since direct web search isn't available in the base OpenAI API,
this module constructs a knowledge-extraction prompt that leverages
the model's training data about known buildings and architectural history.

For production use, this could be extended with:
- Google Custom Search API
- Wikidata/Wikipedia API
- Regional heritage registry APIs (e.g. ЕГРОКН for Russia)
"""

import json
import logging

import requests

from src.prompts import RESEARCH_SYSTEM_PROMPT, RESEARCH_USER_PROMPT

logger = logging.getLogger(__name__)

API_URL = "https://api.openai.com/v1/chat/completions"


class HistoryResearcher:
    """Researches building history and heritage status."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    async def research(self, address: str, style_hint: str = "") -> dict:
        """
        Research building history based on address and visual clues.

        Args:
            address: Full building address.
            style_hint: Architectural style detected by vision analysis.

        Returns:
            Dict with keys: year_built, architect, original_purpose,
            heritage_status, historical_events, neighborhood_context,
            architectural_context, sources, tokens.
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": RESEARCH_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": RESEARCH_USER_PROMPT.format(
                        address=address,
                        style_hint=style_hint,
                    ),
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
            logger.error("Research failed: %s", e)
            return self._fallback_result(str(e))

    @staticmethod
    def _fallback_result(error: str) -> dict:
        return {
            "year_built": "unknown",
            "architect": "unknown",
            "original_purpose": "unknown",
            "heritage_status": "unknown",
            "historical_events": [],
            "neighborhood_context": "",
            "architectural_context": "",
            "sources": [],
            "tokens": 0,
            "error": error,
        }
