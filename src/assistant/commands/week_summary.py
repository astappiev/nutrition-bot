from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from ..meals import MACRO_LABELS, MACRO_SERVING_FIELDS, MACRO_UNITS, MealService, WeekSummary
from ..nutrition import NUTRIENT_LABELS

WEEK_SUMMARY_COMMAND = BotCommand("week_summary", "This week vs last week, plus nutrient coverage")


def _format_delta(this_value: float, prior_value: float | None) -> str:
    if prior_value is None:
        return ""
    delta = this_value - prior_value
    sign = "+" if delta >= 0 else ""
    return f" ({sign}{delta:.0f} vs last week)"


def _format_week_summary(summary: WeekSummary) -> str:
    lines = ["Daily average (this week):"]
    for field_name in MACRO_SERVING_FIELDS:
        this_value = summary.this_week_daily_avg[field_name]
        prior_value = summary.prior_week_daily_avg[field_name] if summary.prior_week_daily_avg else None
        lines.append(
            f"{MACRO_LABELS[field_name]}: {this_value:.0f} {MACRO_UNITS[field_name]}"
            f"{_format_delta(this_value, prior_value)}"
        )
    if summary.prior_week_daily_avg is None:
        lines.append("(No data from the prior week to compare against.)")

    coverage_items = sorted(summary.weekly_norm_coverage.items(), key=lambda item: item[1], reverse=True)
    if coverage_items:
        lines.append("")
        lines.append("Weekly nutrient coverage (% of reference intake):")
        for nutrient, pct in coverage_items:
            lines.append(f"{NUTRIENT_LABELS[nutrient]}: {pct:.0f}% of weekly target")

    return "\n".join(lines)


def build_week_summary_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        summary = await meals.week_summary(user.id)
        await message.reply_text(_format_week_summary(summary))

    return CommandHandler("week_summary", handler)
