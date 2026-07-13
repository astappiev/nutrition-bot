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

from . import i18n
from .auth import build_authorization_gate
from .commands import (
    build_clear_handler,
    build_day_summary_handler,
    build_destroy_handler,
    build_profile_handler,
    build_start_handler,
    build_timezone_callback_handler,
    build_timezone_handler,
    build_week_summary_handler,
)
from .config import Settings
from .conversation import ConversationService, TurnResult
from .meals import MealLogResult, MealService

logger = logging.getLogger(__name__)


def _approval_keyboard(row_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(i18n.t("approve_button", lang), callback_data=f"apr:{row_id}:yes"),
                InlineKeyboardButton(i18n.t("deny_button", lang), callback_data=f"apr:{row_id}:no"),
            ]
        ]
    )


def _format_tool_call(tool_name: str, args: dict) -> str:
    pretty_args = json.dumps(args, indent=2, ensure_ascii=False)
    return f"{tool_name}({pretty_args})"


def _format_approval_text(tool_name: str, args: dict, lang: str) -> str:
    return i18n.t("approval_prompt", lang, call=_format_tool_call(tool_name, args))


def _format_auto_call_text(tool_name: str, args: dict, lang: str) -> str:
    return i18n.t("auto_call_notice", lang, call=_format_tool_call(tool_name, args))


def _format_meal_result(result: MealLogResult, lang: str) -> str:
    if result.error or result.facts is None:
        return result.error or i18n.t("meal_analysis_error", lang)

    facts = result.facts
    lines = [
        facts.food_description,
        i18n.t("meal_serving", lang, desc=facts.serving_description, grams=f"{facts.serving_grams:.0f}"),
        "",
        i18n.t("meal_energy", lang, kcal=f"{facts.energy_kcal_serving:.0f}"),
        i18n.t("meal_protein", lang, p=f"{facts.protein_g_serving:.1f}"),
        i18n.t("meal_fat", lang, f=f"{facts.fat_g_serving:.1f}", sat=f"{facts.saturated_fat_g_serving:.1f}"),
        i18n.t("meal_carb", lang, c=f"{facts.carbohydrate_g_serving:.1f}", s=f"{facts.sugars_g_serving:.1f}"),
        i18n.t("meal_sodium", lang, mg=f"{facts.sodium_mg_serving:.0f}"),
    ]
    if result.highlights:
        lines.append("")
        for highlight in result.highlights:
            verb = i18n.t("nutrient_excellent", lang) if highlight.tier == "excellent" else i18n.t("nutrient_good", lang)
            lines.append(
                i18n.t(
                    "nutrient_source_line",
                    lang,
                    verb=verb,
                    nutrient=i18n.nutrient_label(highlight.nutrient_key, lang),
                    pct=f"{highlight.pct_daily_value:.0f}",
                )
            )
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
        self.application.add_handler(build_clear_handler(self._conversations, self._meals))
        self.application.add_handler(build_profile_handler(self._meals))
        self.application.add_handler(build_timezone_handler(self._meals))
        self.application.add_handler(build_day_summary_handler(self._meals))
        self.application.add_handler(build_week_summary_handler(self._meals))
        self.application.add_handler(build_destroy_handler(self._meals))
        self.application.add_handler(MessageHandler(filters.PHOTO, self._on_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
        self.application.add_handler(CallbackQueryHandler(self._on_approval_callback, pattern=r"^apr:"))
        self.application.add_handler(CallbackQueryHandler(self._on_destroy_callback, pattern=r"^destroy:"))
        self.application.add_handler(build_timezone_callback_handler(self._meals))

    async def _on_message(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None or message.text is None:
            return

        user_id = user.id
        lang = await self._meals.resolve_language(user_id, user.language_code)
        await chat.send_action(ChatAction.TYPING)
        try:
            result = await self._meals.log_text(user_id, message.text)
        except Exception:
            logger.exception("Meal logging failed for user %s", user_id)
            await message.reply_text(i18n.t("generic_error", lang))
            return

        await message.reply_text(_format_meal_result(result, lang))

    async def _on_photo(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None or not message.photo:
            return

        user_id = user.id
        lang = await self._meals.resolve_language(user_id, user.language_code)
        await chat.send_action(ChatAction.TYPING)
        try:
            photo = message.photo[-1]
            file = await photo.get_file()
            image_bytes = bytes(await file.download_as_bytearray())
            result = await self._meals.log_photo(user_id, image_bytes, "image/jpeg", message.caption)
        except Exception:
            logger.exception("Photo meal logging failed for user %s", user_id)
            await message.reply_text(i18n.t("generic_error", lang))
            return

        await message.reply_text(_format_meal_result(result, lang))

    async def _on_destroy_callback(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if query is None or user is None or query.data is None:
            return

        lang = await self._meals.resolve_language(user.id, user.language_code)
        parts = query.data.split(":")
        if parts[1] == "no":
            await query.answer()
            await query.edit_message_text(i18n.t("destroy_cancelled", lang))
            return

        target_user_id = int(parts[2])
        if target_user_id != user.id:
            await query.answer(i18n.t("destroy_not_yours", lang), show_alert=True)
            return

        await self._meals.destroy(user.id)
        await query.answer()
        await query.edit_message_text(i18n.t("destroy_done", lang))

    async def _on_approval_callback(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if query is None or user is None or query.data is None:
            return

        user_id = user.id
        lang = await self._meals.resolve_language(user_id, user.language_code)
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
            await query.answer(i18n.t("approval_something_wrong", lang), show_alert=True)
            return

        await query.answer()
        verdict = i18n.t("approval_verdict_approved", lang) if approved else i18n.t("approval_verdict_denied", lang)
        await query.edit_message_text(f"{verdict}: {_format_tool_call(tool_name, args)}")

        chat = update.effective_chat
        if turn_result is not None and chat is not None:
            await self._deliver(chat.id, turn_result, lang)

    async def _deliver(self, chat_id: int, turn_result: TurnResult, lang: str) -> None:
        for call in turn_result.auto_calls:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=_format_auto_call_text(call.tool_name, call.args, lang),
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
                text=_format_approval_text(approval.tool_name, approval.args, lang),
                reply_markup=_approval_keyboard(approval.row_id, lang),
            )

    def run(self) -> None:
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
