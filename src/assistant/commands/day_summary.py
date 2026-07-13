from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import i18n
from ..meals import MACRO_SERVING_FIELDS, DaySummary, MealService

DAY_SUMMARY_COMMAND = BotCommand("day_summary", "Totals for the last day")


def _format_day_summary(summary: DaySummary, lang: str) -> str:
    if summary.meal_count == 0:
        return i18n.t("day_summary_empty", lang)

    lines = [i18n.t("meals_logged", lang, count=summary.meal_count), ""]
    for field_name in MACRO_SERVING_FIELDS:
        value = summary.totals[field_name]
        lines.append(f"{i18n.macro_label(field_name, lang)}: {value:.0f} {i18n.macro_unit(field_name, lang)}")
    return "\n".join(lines)


def build_day_summary_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        summary = await meals.day_summary(user.id)
        await message.reply_text(_format_day_summary(summary, lang))

    return CommandHandler("day_summary", handler)
