from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from .config import Settings


def build_authorization_gate(settings: Settings):
    """Global pre-handler: rejects updates from users not in ALLOWED_USER_IDS.

    Registered in an earlier handler group (see telegram_bot.py) so it runs
    before every other handler; raises ApplicationHandlerStop to prevent any
    command/message/callback handler from running for a denied update.
    """

    async def gate(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is not None and settings.is_user_allowed(user.id):
            return

        if update.callback_query is not None:
            await update.callback_query.answer("Not authorized.")
        elif update.effective_message is not None:
            await update.effective_message.reply_text("You are not authorized to use this bot.")
        raise ApplicationHandlerStop

    return gate
