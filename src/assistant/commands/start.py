from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import i18n
from ..meals import MealService

START_COMMAND = BotCommand("start", "Show help and available commands")


def build_start_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        settings = await meals.get_settings(user.id)
        text = i18n.t("help_text", lang)
        if settings.sex is None or settings.age is None:
            text += i18n.t("profile_nudge", lang)

        await message.reply_text(text)

    return CommandHandler(["start", "help"], handler)
