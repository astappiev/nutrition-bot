from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from ..meals import MealService

TIMEZONE_COMMAND = BotCommand("timezone", "Set your IANA timezone, e.g. Europe/Berlin")

USAGE = "Usage: /timezone <IANA name>\nExample: /timezone Europe/Berlin"


def build_timezone_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        args = context.args or []
        if len(args) != 1:
            await message.reply_text(USAGE)
            return

        tz_name = args[0]
        try:
            ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            await message.reply_text(f"Unknown timezone: {tz_name}")
            return

        await meals.set_timezone(user.id, tz_name)
        await message.reply_text(f"Timezone set to {tz_name}.")

    return CommandHandler("timezone", handler)
