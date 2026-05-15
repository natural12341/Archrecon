"""
Telegram message handlers.

Manages the two-step interaction flow:
  1. User sends a photo of a building
  2. User provides the address
  3. Bot runs the analysis pipeline and returns a report
"""

import base64
import logging
from io import BytesIO

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from src.vision_analyzer import VisionAnalyzer
from src.research import HistoryResearcher
from src.report_builder import ReportBuilder

logger = logging.getLogger(__name__)
router = Router()


class AnalysisFlow(StatesGroup):
    """FSM states for the analysis conversation."""
    waiting_for_address = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🏛 *ArchRecon — Pre-project Building Analysis*\n\n"
        "Send me a photo of a building, and I'll help you create "
        "a pre-project analysis report.\n\n"
        "*How to use:*\n"
        "1. Send a photo of the building\n"
        "2. I'll ask for the address\n"
        "3. Get a full report: style, history, construction, condition\n\n"
        "📸 Send a photo to start.",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "*Available commands:*\n"
        "/start — Introduction\n"
        "/help — This message\n"
        "/cancel — Cancel current analysis\n\n"
        "*Tips for best results:*\n"
        "• Photograph the full facade, not just a detail\n"
        "• Daytime photos work better\n"
        "• Include the full street address with city",
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Nothing to cancel. Send a photo to start.")
        return
    await state.clear()
    await message.answer("Analysis cancelled. Send a new photo whenever you're ready.")


@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext, bot):
    """Receive building photo and ask for address."""
    await message.answer("📷 Photo received. Processing image...")

    # Download the highest resolution photo
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_bytes = BytesIO()
    await bot.download_file(file.file_path, photo_bytes)

    # Encode to base64 for Vision API
    photo_b64 = base64.b64encode(photo_bytes.getvalue()).decode("utf-8")

    # Store photo and ask for address
    await state.set_state(AnalysisFlow.waiting_for_address)
    await state.update_data(photo_b64=photo_b64)

    await message.answer(
        "📍 Now send me the *address* of this building.\n\n"
        "Include street, building number, and city.\n"
        "Example: _ул. Красная 5, Краснодар_",
    )


@router.message(AnalysisFlow.waiting_for_address)
async def handle_address(message: Message, state: FSMContext, bot):
    """Receive address and run full analysis pipeline."""
    address = message.text.strip()
    if not address or len(address) < 5:
        await message.answer("Please provide a full address (street, number, city).")
        return

    data = await state.get_data()
    photo_b64 = data.get("photo_b64")

    if not photo_b64:
        await message.answer("Photo was lost. Please send the photo again.")
        await state.clear()
        return

    api_key = bot._dispatcher["openai_api_key"] if hasattr(bot, "_dispatcher") else None
    # Fallback: get from dispatcher via router context
    if not api_key:
        import os
        api_key = os.getenv("OPENAI_API_KEY")

    await message.answer("🔍 Analyzing building...\nThis may take 30-60 seconds.")

    try:
        # ── Step 1: Vision analysis ──────────────────────────────────
        vision = VisionAnalyzer(api_key=api_key)
        visual_data = await vision.analyze(photo_b64=photo_b64, address=address)
        logger.info("Vision analysis complete: %s tokens", visual_data.get("tokens", 0))

        # ── Step 2: Historical research ──────────────────────────────
        researcher = HistoryResearcher(api_key=api_key)
        history_data = await researcher.research(
            address=address,
            style_hint=visual_data.get("style", ""),
        )
        logger.info("Historical research complete: %s tokens", history_data.get("tokens", 0))

        # ── Step 3: Compile report ───────────────────────────────────
        builder = ReportBuilder(api_key=api_key)
        report = await builder.build(
            address=address,
            visual=visual_data,
            history=history_data,
        )
        logger.info("Report compiled: %s tokens", report.get("tokens", 0))

        total_tokens = (
            visual_data.get("tokens", 0)
            + history_data.get("tokens", 0)
            + report.get("tokens", 0)
        )
        logger.info("Total pipeline tokens: %s", total_tokens)

        # Send report (split if too long for Telegram)
        report_text = report.get("text", "Analysis failed.")
        await _send_long_message(message, report_text)

    except Exception as e:
        logger.error("Analysis failed: %s", e, exc_info=True)
        await message.answer(
            "⚠️ Analysis failed. This might be due to:\n"
            "• API rate limits\n"
            "• Unclear photo\n"
            "• Address not found\n\n"
            "Please try again with /cancel and a new photo."
        )

    await state.clear()


@router.message()
async def handle_unknown(message: Message):
    """Handle any other message."""
    await message.answer(
        "📸 Send me a *photo* of a building to start the analysis.\n"
        "Use /help for instructions.",
    )


async def _send_long_message(message: Message, text: str, chunk_size: int = 4000):
    """Split long messages to fit Telegram's 4096 char limit."""
    if len(text) <= chunk_size:
        await message.answer(text)
        return

    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break

        # Find a good split point (paragraph or line break)
        split_at = text.rfind("\n\n", 0, chunk_size)
        if split_at == -1:
            split_at = text.rfind("\n", 0, chunk_size)
        if split_at == -1:
            split_at = chunk_size

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    for chunk in chunks:
        await message.answer(chunk)
