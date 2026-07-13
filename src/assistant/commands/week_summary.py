from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import i18n
from ..meals import MACRO_SERVING_FIELDS, MealService, WeekSummary

WEEK_SUMMARY_COMMAND = BotCommand("week_summary", "This week vs last week, plus nutrient coverage")


def _format_delta(this_value: float, prior_value: float | None, lang: str) -> str:
    if prior_value is None:
        return ""
    delta = this_value - prior_value
    sign = "+" if delta >= 0 else ""
    return i18n.t("week_delta_suffix", lang, sign=sign, delta=f"{delta:.0f}")


def _format_week_summary(summary: WeekSummary, lang: str) -> str:
    lines = [i18n.t("week_daily_avg_header", lang)]
    for field_name in MACRO_SERVING_FIELDS:
        this_value = summary.this_week_daily_avg[field_name]
        prior_value = summary.prior_week_daily_avg[field_name] if summary.prior_week_daily_avg else None
        lines.append(
            f"{i18n.macro_label(field_name, lang)}: {this_value:.0f} {i18n.macro_unit(field_name, lang)}"
            f"{_format_delta(this_value, prior_value, lang)}"
        )
    if summary.prior_week_daily_avg is None:
        lines.append(i18n.t("week_no_prior_data", lang))

    coverage_items = sorted(summary.weekly_norm_coverage.items(), key=lambda item: item[1], reverse=True)
    if coverage_items:
        lines.append("")
        lines.append(i18n.t("week_coverage_header", lang))
        for nutrient, pct in coverage_items:
            lines.append(i18n.t("week_coverage_line", lang, nutrient=i18n.nutrient_label(nutrient, lang), pct=f"{pct:.0f}"))

    return "\n".join(lines)


def build_week_summary_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        summary = await meals.week_summary(user.id)
        await message.reply_text(_format_week_summary(summary, lang))

    return CommandHandler("week_summary", handler)
