"""
ArchRecon Bot — Pre-project building analysis via Telegram.

Send a photo of a building + its address, and get a structured
architectural report: style, era, construction, history,
heritage status, condition assessment, and design implications.

Usage:
    python bot.py
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from src.handlers import router

load_dotenv()


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found. Copy .env.example to .env and add your token.")
        sys.exit(1)

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OPENAI_API_KEY not found. Add it to your .env file.")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    dp = Dispatcher()
    dp["openai_api_key"] = openai_key
    dp.include_router(router)

    logging.info("ArchRecon Bot starting...")
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
