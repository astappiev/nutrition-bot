from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from .. import i18n
from ..meals import MealService

TIMEZONE_COMMAND = BotCommand("timezone", "Set your IANA timezone, e.g. Europe/Berlin")

# A practical, non-exhaustive spread of IANA zones shown as a picker when /timezone
# is called with no argument; users who want something else can still type
# /timezone <IANA name> directly.
COMMON_TIMEZONES = (
    "UTC",
    "Europe/Berlin",
    "Europe/Kyiv",
    "Europe/London",
    "America/New_York",
    "America/Los_Angeles",
    "Asia/Dubai",
    "Asia/Kolkata",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Australia/Sydney",
)


def _timezone_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(name, callback_data=f"tz:{name}")]
        for name in COMMON_TIMEZONES
    ]
    return InlineKeyboardMarkup(rows)


def build_timezone_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        args = context.args or []
        if len(args) != 1:
            await message.reply_text(i18n.t("timezone_usage", lang), reply_markup=_timezone_keyboard())
            return

        tz_name = args[0]
        try:
            ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            await message.reply_text(i18n.t("timezone_unknown", lang, tz=tz_name))
            return

        await meals.set_timezone(user.id, tz_name)
        await message.reply_text(i18n.t("timezone_set", lang, tz=tz_name))

    return CommandHandler("timezone", handler)


def build_timezone_callback_handler(meals: MealService) -> CallbackQueryHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if query is None or user is None or query.data is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        tz_name = query.data.split(":", maxsplit=1)[1]
        await meals.set_timezone(user.id, tz_name)
        await query.answer()
        await query.edit_message_text(i18n.t("timezone_set", lang, tz=tz_name))

    return CallbackQueryHandler(handler, pattern=r"^tz:")
