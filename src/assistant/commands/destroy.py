from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

DESTROY_COMMAND = BotCommand("destroy", "Delete all your logged nutrition data")


def _destroy_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Yes, delete everything", callback_data=f"destroy:yes:{user_id}"),
                InlineKeyboardButton("Cancel", callback_data="destroy:no"),
            ]
        ]
    )


def build_destroy_handler() -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        await message.reply_text(
            "This will permanently delete all your logged meals and reset your profile/timezone. "
            "Continue?",
            reply_markup=_destroy_keyboard(user.id),
        )

    return CommandHandler("destroy", handler)
