import json
import logging

import telegramify_markdown
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    filters,
)

from .auth import build_authorization_gate
from .commands import (
    build_clear_handler,
    build_day_summary_handler,
    build_destroy_handler,
    build_profile_handler,
    build_start_handler,
    build_timezone_handler,
    build_week_summary_handler,
)
from .config import Settings
from .conversation import ConversationService, TurnResult
from .meals import MealLogResult, MealService

logger = logging.getLogger(__name__)


def _approval_keyboard(row_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Approve", callback_data=f"apr:{row_id}:yes"),
                InlineKeyboardButton("Deny", callback_data=f"apr:{row_id}:no"),
            ]
        ]
    )


def _format_tool_call(tool_name: str, args: dict) -> str:
    pretty_args = json.dumps(args, indent=2, ensure_ascii=False)
    return f"{tool_name}({pretty_args})"


def _format_approval_text(tool_name: str, args: dict) -> str:
    return f"The assistant wants to call a tool:\n\n{_format_tool_call(tool_name, args)}\n\nApprove this action?"


def _format_auto_call_text(tool_name: str, args: dict) -> str:
    return f"Called tool (auto-approved):\n\n{_format_tool_call(tool_name, args)}"


def _format_meal_result(result: MealLogResult) -> str:
    if result.error or result.facts is None:
        return result.error or "Something went wrong analyzing that."

    facts = result.facts
    lines = [
        facts.food_description,
        f"Serving: {facts.serving_description} ({facts.serving_grams:.0f} g)",
        "",
        f"Energy: {facts.energy_kcal_serving:.0f} kcal",
        f"Protein: {facts.protein_g_serving:.1f} g",
        f"Fat: {facts.fat_g_serving:.1f} g (sat. {facts.saturated_fat_g_serving:.1f} g)",
        f"Carbohydrate: {facts.carbohydrate_g_serving:.1f} g (sugars {facts.sugars_g_serving:.1f} g)",
        f"Sodium: {facts.sodium_mg_serving:.0f} mg",
    ]
    if result.highlights:
        lines.append("")
        for highlight in result.highlights:
            verb = "Excellent" if highlight.tier == "excellent" else "Good"
            lines.append(f"{verb} source of {highlight.nutrient} ({highlight.pct_daily_value:.0f}% DV)")
    return "\n".join(lines)


class TelegramBot:
    def __init__(self, settings: Settings, conversations: ConversationService, meals: MealService):
        self._settings = settings
        self._conversations = conversations
        self._meals = meals
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self._register_handlers()

    def _register_handlers(self) -> None:
        # group=-1 runs before the default group (0); the gate raises
        # ApplicationHandlerStop to block every handler below for denied users.
        self.application.add_handler(TypeHandler(Update, build_authorization_gate(self._settings)), group=-1)

        self.application.add_handler(build_start_handler(self._meals))
        self.application.add_handler(build_clear_handler(self._conversations))
        self.application.add_handler(build_profile_handler(self._meals))
        self.application.add_handler(build_timezone_handler(self._meals))
        self.application.add_handler(build_day_summary_handler(self._meals))
        self.application.add_handler(build_week_summary_handler(self._meals))
        self.application.add_handler(build_destroy_handler())
        self.application.add_handler(MessageHandler(filters.PHOTO, self._on_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
        self.application.add_handler(CallbackQueryHandler(self._on_approval_callback, pattern=r"^apr:"))
        self.application.add_handler(CallbackQueryHandler(self._on_destroy_callback, pattern=r"^destroy:"))

    async def _on_message(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None or message.text is None:
            return

        user_id = user.id
        await chat.send_action(ChatAction.TYPING)
        try:
            result = await self._meals.log_text(user_id, message.text)
        except Exception:
            logger.exception("Meal logging failed for user %s", user_id)
            await message.reply_text("Something went wrong handling that. Please try again.")
            return

        await message.reply_text(_format_meal_result(result))

    async def _on_photo(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None or not message.photo:
            return

        user_id = user.id
        await chat.send_action(ChatAction.TYPING)
        try:
            photo = message.photo[-1]
            file = await photo.get_file()
            image_bytes = bytes(await file.download_as_bytearray())
            result = await self._meals.log_photo(user_id, image_bytes, "image/jpeg", message.caption)
        except Exception:
            logger.exception("Photo meal logging failed for user %s", user_id)
            await message.reply_text("Something went wrong handling that. Please try again.")
            return

        await message.reply_text(_format_meal_result(result))

    async def _on_destroy_callback(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if query is None or user is None or query.data is None:
            return

        parts = query.data.split(":")
        if parts[1] == "no":
            await query.answer()
            await query.edit_message_text("Cancelled. Your data is safe.")
            return

        target_user_id = int(parts[2])
        if target_user_id != user.id:
            await query.answer("This confirmation isn't yours.", show_alert=True)
            return

        await self._meals.destroy(user.id)
        await query.answer()
        await query.edit_message_text("All your nutrition data has been deleted.")

    async def _on_approval_callback(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if query is None or user is None or query.data is None:
            return

        user_id = user.id
        _, row_id_str, decision = query.data.split(":", maxsplit=2)
        approved = decision == "yes"

        try:
            tool_name, args, turn_result = await self._conversations.resolve_approval(
                user_id, int(row_id_str), approved
            )
        except ValueError as exc:
            await query.answer(str(exc), show_alert=True)
            return
        except Exception:
            logger.exception("Failed to resolve approval %s for user %s", row_id_str, user_id)
            await query.answer("Something went wrong.", show_alert=True)
            return

        await query.answer()
        verdict = "APPROVED" if approved else "DENIED"
        await query.edit_message_text(f"{verdict}: {_format_tool_call(tool_name, args)}")

        chat = update.effective_chat
        if turn_result is not None and chat is not None:
            await self._deliver(chat.id, turn_result)

    async def _deliver(self, chat_id: int, turn_result: TurnResult) -> None:
        for call in turn_result.auto_calls:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=_format_auto_call_text(call.tool_name, call.args),
            )
        if turn_result.reply:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=telegramify_markdown.markdownify(turn_result.reply),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        for approval in turn_result.approvals:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=_format_approval_text(approval.tool_name, approval.args),
                reply_markup=_approval_keyboard(approval.row_id),
            )

    def run(self) -> None:
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
