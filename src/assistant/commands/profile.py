from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from ..meals import MealService

PROFILE_COMMAND = BotCommand("profile", "Set your sex and age for personalized nutrient targets")

USAGE = "Usage: /profile <male|female> <age>\nExample: /profile female 29"


def build_profile_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        args = context.args or []
        if len(args) != 2:
            await message.reply_text(USAGE)
            return

        sex = args[0].lower()
        if sex not in ("male", "female"):
            await message.reply_text(USAGE)
            return

        if not args[1].isdigit() or not (1 <= int(args[1]) <= 120):
            await message.reply_text(USAGE)
            return
        age = int(args[1])

        await meals.set_profile(user.id, sex, age)
        await message.reply_text(f"Profile set: {sex}, age {age}.")

    return CommandHandler("profile", handler)
