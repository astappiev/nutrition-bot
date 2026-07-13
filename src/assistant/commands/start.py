from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from ..meals import MealService

START_COMMAND = BotCommand("start", "Show help and available commands")

HELP_TEXT = (
    "Hi! I'm Nutrition Couch. Send me a food photo or describe what you ate, any time of "
    "day, and I'll estimate its nutrition facts and log it.\n\n"
    "Commands:\n"
    "/profile <male|female> <age> - set your profile for personalized nutrient targets\n"
    "/timezone <IANA name> - set your timezone, e.g. Europe/Berlin\n"
    "/day_summary - totals for the last day\n"
    "/week_summary - this week vs last week, plus nutrient coverage\n"
    "/destroy - delete all your logged data"
)

PROFILE_NUDGE = "\n\nSet your profile for personalized nutrient targets: /profile <male|female> <age>"


def build_start_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        settings = await meals.get_settings(user.id)
        text = HELP_TEXT
        if settings.sex is None or settings.age is None:
            text += PROFILE_NUDGE

        await message.reply_text(text)

    return CommandHandler(["start", "help"], handler)
