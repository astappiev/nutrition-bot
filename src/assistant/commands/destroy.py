from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import i18n
from ..meals import MealService

DESTROY_COMMAND = BotCommand("destroy", "Delete all your logged nutrition data")


def _destroy_keyboard(user_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(i18n.t("destroy_yes", lang), callback_data=f"destroy:yes:{user_id}"),
                InlineKeyboardButton(i18n.t("destroy_cancel", lang), callback_data="destroy:no"),
            ]
        ]
    )


def build_destroy_handler(meals: MealService) -> CommandHandler:
    async def handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        lang = await meals.resolve_language(user.id, user.language_code)
        await message.reply_text(
            i18n.t("destroy_confirm", lang),
            reply_markup=_destroy_keyboard(user.id, lang),
        )

    return CommandHandler("destroy", handler)
