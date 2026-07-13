# Nutrition Couch

A Telegram bot for effortless food logging. Send it a photo of what you're eating, or just
describe it in text, any time of day - it estimates nutrition facts (macros plus whichever
vitamins/minerals it can reasonably infer) and logs the meal. `/day_summary` and
`/week_summary` roll those meals up into totals.

> The bundled reference-intake table (used for "good/excellent source of X" callouts and
> weekly coverage %) is a generic approximation drawn from standard NIH ODS / FDA figures.
> It's a reasonableness yardstick, not medical or dietary advice.

## How it's put together

```
src/assistant/
  config.py        Settings loaded from .env / environment
  db.py             SQLite schema + repository functions (aiosqlite, no ORM)
  nutrition.py      One-shot Pydantic AI agent that turns a photo/text into NutritionFacts,
                    plus the reference-intake tables used for %DV callouts
  meals.py          MealService: logs meals, builds day/week summaries, owns user_settings
  commands/         Telegram command handlers (/start, /profile, /timezone, /day_summary,
                    /week_summary, /destroy, /clear)
  telegram_bot.py   python-telegram-bot wiring: text/photo handlers, inline-keyboard confirms
  __main__.py       Wires everything together and starts polling

  agent.py          Kept, unwired: approval-gated MCP toolset agent (see "Extending")
  conversation.py   Kept, unwired: per-user turn logic for the agent above
```

Each meal (text or photo) is a single isolated call to the nutrition agent - no conversation
history in or out, so meal logging never touches `conversations`/`messages`/`agent_state`/
`tool_calls`. Every logged meal is stored in `meals`, and each user's timezone/profile
(biological sex + age, used to personalize nutrient targets) lives in `user_settings`.

## Setup

```
cp .env.example .env   # fill in TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, ALLOWED_USER_IDS
uv sync
```

```
uv run python -m assistant
```

Message the bot on Telegram:

- `/start` - help text; nudges you to `/profile` if unset.
- `/profile <male|female> <age>` - personalizes nutrient targets. Optional - logging works
  without it, falling back to a generic reference profile.
- `/timezone <IANA name>` - sets your timezone (e.g. `Europe/Berlin`), used to label meals
  Breakfast/Lunch/Dinner/Snack and to bucket day/week windows.
- Send a food photo or describe a meal in text - get back an estimated nutrition breakdown,
  logged automatically.
- `/day_summary` - totals since your last `/day_summary` call (or the last 24h).
- `/week_summary` - this week's daily macro averages vs. last week's, plus % of the weekly
  reference intake covered per nutrient.
- `/destroy` - deletes all your logged meals and resets your profile/timezone, after
  confirmation.

## Extending

This started as a general-purpose Telegram assistant with Pydantic AI tool orchestration
(MCP toolsets gated behind a Telegram Approve/Deny prompt). That machinery - `agent.py`,
`conversation.py`, and the `conversations`/`messages`/`agent_state`/`tool_calls` tables - is
kept in place but entirely unwired from the nutrition-logging flow, for future tool-based
features. `/clear` still exercises it end-to-end even though nothing currently drives it into
a live conversation.

- Add MCP servers: `MCP_SERVERS` accepts either a comma-separated list of URLs (no auth), or
  a JSON array of `{"url", "headers"}` objects for servers that need an auth header.
- Swap the nutrition/chat model: change `LLM_MODEL` (any Pydantic AI model string that
  accepts image input) and set the matching API key env var.
