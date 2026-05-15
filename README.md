# 🏛 ArchRecon Bot

Telegram bot for pre-project building analysis. Send a photo of a building and its address — get a structured architectural report covering style, history, construction, condition, and heritage status.

Built as a practical tool for architects starting project work on existing buildings.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.x-green)
![License](https://img.shields.io/badge/License-MIT-green)

## What It Does

The bot runs a 3-stage AI pipeline:

1. **Vision Analysis** — Sends the photo to OpenAI Vision API to extract architectural characteristics: style, era, materials, construction type, floor count, condition, decorative features
2. **Historical Research** — Uses LLM knowledge to research the building's history: architect, construction date, heritage status, alterations, neighborhood context
3. **Report Assembly** — Synthesizes both sources into a structured pre-project report in Russian, formatted for Telegram

### Sample Interaction

```
User: [sends photo of a building]
Bot:  📷 Photo received. Processing image...
      📍 Now send me the address of this building.

User: ул. Красная 5, Краснодар

Bot:  🔍 Analyzing building...

      🏛 *Предпроектный анализ*
      📍 ул. Красная 5, Краснодар

      *Архитектурные характеристики*
      Стиль: Сталинский неоклассицизм
      Период: конец 1940-х — начало 1950-х
      Этажность: 5 этажей
      ...

      *Историческая справка*
      ...

      *Рекомендации для проектирования*
      ...
```

## Architecture

```
bot.py                    Entry point, aiogram dispatcher setup
src/
├── handlers.py           Telegram handlers + FSM conversation flow
├── vision_analyzer.py    Photo → architectural characteristics (Vision API)
├── research.py           Address → historical data (Chat API)
├── report_builder.py     Visual + History → structured report
└── prompts.py            All prompt templates (centralized)
```

### Pipeline Flow

```
Photo + Address
       │
       ├──→ VisionAnalyzer ──→ {style, era, materials, condition, ...}
       │                                    │
       └──→ HistoryResearcher ──→ {year, architect, heritage, ...}
                                            │
                                            ▼
                                     ReportBuilder
                                            │
                                            ▼
                                  Telegram Markdown Report
```

### Design Decisions

**Centralized prompts** (`src/prompts.py`): All system and user prompts live in one file. This makes iteration fast — you can tune a prompt without touching any logic code.

**JSON structured outputs**: Vision and research stages return JSON (via OpenAI's `response_format`), ensuring reliable parsing. The report stage outputs free-form Markdown for readability.

**FSM conversation flow**: Uses aiogram's finite state machine to manage the two-step interaction (photo → address) cleanly. Supports `/cancel` at any point.

**Emergency fallback**: If the final LLM call fails, the bot still returns a basic report from raw structured data rather than showing an error.

## Setup

### 1. Create a Telegram Bot

Talk to [@BotFather](https://t.me/BotFather) on Telegram:
```
/newbot
→ Choose a name: ArchRecon
→ Choose a username: archrecon_bot
→ Copy the token
```

### 2. Install & Configure

```bash
git clone https://github.com/YOUR_USERNAME/archrecon-bot.git
cd archrecon-bot
pip install -r requirements.txt

cp .env.example .env
# Edit .env: add TELEGRAM_BOT_TOKEN and OPENAI_API_KEY
```

### 3. Run

```bash
python bot.py
```

## Requirements

- Python 3.10+
- Telegram Bot Token (free from BotFather)
- OpenAI API key (needs access to `gpt-4o-mini` or `gpt-4o` with vision)

## Limitations & Future Work

- Historical research relies on LLM training data, not live web search — accuracy varies for lesser-known buildings
- Single-photo analysis; multiple angles would improve accuracy
- No OCR for plaques or signage visible in photos
- Planned: integration with heritage registries (ЕГРОКН), Google Street View for context, multi-photo support, PDF report export

## License

MIT
