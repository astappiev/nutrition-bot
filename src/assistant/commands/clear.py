from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ContextTypes

from ..conversation import ConversationService

CLEAR_COMMAND = BotCommand("clear", "Start a new conversation")


def build_clear_handler(conversations: ConversationService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        await conversations.discard(user.id)
        await message.reply_text("Conversation cleared.")

    return CommandHandler(["clear", "new"], handler)
