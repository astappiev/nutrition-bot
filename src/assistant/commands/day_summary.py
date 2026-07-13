from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from ..meals import MACRO_LABELS, MACRO_SERVING_FIELDS, MACRO_UNITS, DaySummary, MealService

DAY_SUMMARY_COMMAND = BotCommand("day_summary", "Totals for the last day")


def _format_day_summary(summary: DaySummary) -> str:
    if summary.meal_count == 0:
        return "No meals logged since the last summary."

    lines = [f"Meals logged: {summary.meal_count}", ""]
    for field_name in MACRO_SERVING_FIELDS:
        value = summary.totals[field_name]
        lines.append(f"{MACRO_LABELS[field_name]}: {value:.0f} {MACRO_UNITS[field_name]}")
    return "\n".join(lines)


def build_day_summary_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        summary = await meals.day_summary(user.id)
        await message.reply_text(_format_day_summary(summary))

    return CommandHandler("day_summary", handler)
