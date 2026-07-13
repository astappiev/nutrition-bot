from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import i18n
from ..conversation import ConversationService
from ..meals import MealService

CLEAR_COMMAND = BotCommand("clear", "Start a new conversation")


def build_clear_handler(conversations: ConversationService, meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        await conversations.discard(user.id)
        await message.reply_text(i18n.t("clear_cleared", lang))

    return CommandHandler(["clear", "new"], handler)
