from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import i18n
from ..meals import MealService

PROFILE_COMMAND = BotCommand("profile", "Set your sex and age for personalized nutrient targets")


def build_profile_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        args = context.args or []
        if len(args) != 2:
            await message.reply_text(i18n.t("profile_usage", lang))
            return

        sex = args[0].lower()
        if sex not in ("male", "female"):
            await message.reply_text(i18n.t("profile_usage", lang))
            return

        if not args[1].isdigit() or not (1 <= int(args[1]) <= 120):
            await message.reply_text(i18n.t("profile_usage", lang))
            return
        age = int(args[1])

        await meals.set_profile(user.id, sex, age)
        await message.reply_text(i18n.t("profile_set", lang, sex=sex, age=age))

    return CommandHandler("profile", handler)
