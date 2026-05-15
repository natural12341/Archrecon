"""
Report builder.

Combines visual analysis and historical research into a structured
pre-project report formatted for Telegram (Markdown).

The final LLM call synthesizes all data into a coherent document
with sections matching standard pre-project analysis requirements.
"""

import json
import logging

import requests

from src.prompts import REPORT_SYSTEM_PROMPT, REPORT_USER_PROMPT

logger = logging.getLogger(__name__)

API_URL = "https://api.openai.com/v1/chat/completions"


class ReportBuilder:
    """Assembles the final pre-project analysis report."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    async def build(self, address: str, visual: dict, history: dict) -> dict:
        """
        Build a complete pre-project analysis report.

        Args:
            address: Building address.
            visual: Output from VisionAnalyzer.
            history: Output from HistoryResearcher.

        Returns:
            Dict with keys: text (markdown report), tokens.
        """
        # Remove token counts before sending to LLM
        visual_clean = {k: v for k, v in visual.items() if k != "tokens"}
        history_clean = {k: v for k, v in history.items() if k != "tokens"}

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": REPORT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": REPORT_USER_PROMPT.format(
                        address=address,
                        visual_data=json.dumps(visual_clean, ensure_ascii=False, indent=2),
                        history_data=json.dumps(history_clean, ensure_ascii=False, indent=2),
                    ),
                },
            ],
            "temperature": 0.4,
            "max_tokens": 3000,
        }

        try:
            resp = self.session.post(API_URL, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)

            return {"text": content, "tokens": total_tokens}

        except requests.RequestException as e:
            logger.error("Report generation failed: %s", e)
            return {
                "text": self._emergency_report(address, visual, history),
                "tokens": 0,
            }

    @staticmethod
    def _emergency_report(address: str, visual: dict, history: dict) -> str:
        """Generate a basic report without LLM if API fails."""
        return (
            f"🏛 *Pre-Project Analysis*\n"
            f"📍 {address}\n\n"
            f"*Style:* {visual.get('style', 'N/A')}\n"
            f"*Era:* {visual.get('era', 'N/A')}\n"
            f"*Floors:* {visual.get('floors', 'N/A')}\n"
            f"*Condition:* {visual.get('condition', 'N/A')}\n\n"
            f"*Year built:* {history.get('year_built', 'N/A')}\n"
            f"*Architect:* {history.get('architect', 'N/A')}\n"
            f"*Heritage:* {history.get('heritage_status', 'N/A')}\n\n"
            f"_Full LLM report unavailable. Raw data shown above._"
        )
