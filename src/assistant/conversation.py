import asyncio
import json
import logging
from dataclasses import dataclass, field

from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults, ToolDenied
from pydantic_ai.messages import ModelMessagesTypeAdapter, ToolCallPart, ToolReturnPart
from pydantic_core import to_json

from .db import Database

logger = logging.getLogger(__name__)


@dataclass
class PendingApproval:
    row_id: int
    tool_name: str
    args: dict


@dataclass
class ToolCallNotice:
    tool_name: str
    args: dict


@dataclass
class TurnResult:
    reply: str | None = None
    approvals: list[PendingApproval] = field(default_factory=list)
    auto_calls: list[ToolCallNotice] = field(default_factory=list)


def _extract_auto_tool_calls(messages: list, *, exclude_ids: frozenset[str] = frozenset()) -> list[ToolCallNotice]:
    """Tool calls from this run step that executed immediately (auto-approved), i.e. calls that
    already have a matching `ToolReturnPart` in the same message batch. Calls still awaiting
    approval have no return part yet - they show up as `PendingApproval` instead. `exclude_ids`
    filters out calls that just went through the user Approve/Deny flow on this same resume, so
    they aren't double-reported as auto-approved.
    """
    calls_by_id: dict[str, ToolCallPart] = {}
    returned_ids: set[str] = set()
    for message in messages:
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolCallPart):
                calls_by_id[part.tool_call_id] = part
            elif isinstance(part, ToolReturnPart):
                returned_ids.add(part.tool_call_id)

    return [
        ToolCallNotice(tool_name=call.tool_name, args=call.args_as_dict())
        for call_id, call in calls_by_id.items()
        if call_id in returned_ids and call_id not in exclude_ids
    ]


class ConversationService:
    """Runs Pydantic AI turns for each Telegram user and persists everything to SQLite.

    Every tool call is wrapped as `approval_required`, so an agent run either
    finishes with plain text, or pauses with `DeferredToolRequests`. In the
    latter case we store one row per pending call and wait for the user to
    press Approve/Deny before resuming the run with `deferred_tool_results`.
    """

    def __init__(self, db: Database, agent: Agent):
        self._db = db
        self._agent = agent
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock_for(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def _load_history(self, conversation_id: int) -> list:
        raw = await self._db.load_history_json(conversation_id)
        return ModelMessagesTypeAdapter.validate_json(raw) if raw else []

    async def _save_history(self, conversation_id: int, messages: list) -> None:
        await self._db.save_history_json(conversation_id, to_json(messages).decode("utf-8"))

    async def _finish(
        self, conversation_id: int, result, *, exclude_auto_call_ids: frozenset[str] = frozenset()
    ) -> TurnResult:
        await self._save_history(conversation_id, result.all_messages())
        auto_calls = _extract_auto_tool_calls(result.new_messages(), exclude_ids=exclude_auto_call_ids)
        for call in auto_calls:
            logger.info("conversation %s auto-approved call: %s(%s)", conversation_id, call.tool_name, call.args)

        if isinstance(result.output, DeferredToolRequests):
            approvals = [
                PendingApproval(
                    row_id=await self._db.create_tool_call(
                        conversation_id, call.tool_call_id, call.tool_name, call.args
                    ),
                    tool_name=call.tool_name,
                    args=call.args,
                )
                for call in result.output.approvals
            ]
            for approval in approvals:
                logger.info(
                    "conversation %s pending approval row %s: %s(%s)",
                    conversation_id,
                    approval.row_id,
                    approval.tool_name,
                    approval.args,
                )
            return TurnResult(reply=None, approvals=approvals, auto_calls=auto_calls)

        reply = result.output
        await self._db.log_message(conversation_id, "assistant", reply)
        logger.info("conversation %s assistant reply: %s", conversation_id, reply)
        return TurnResult(reply=reply, auto_calls=auto_calls)

    async def handle_message(self, user_id: int, text: str) -> TurnResult:
        async with self._lock_for(user_id):
            conversation = await self._db.get_or_open_conversation(user_id)
            if await self._db.count_pending_tool_calls(conversation.id) > 0:
                logger.info("user %s message rejected: pending approvals on conversation %s", user_id, conversation.id)
                return TurnResult(reply="Please Approve/Deny the pending request(s) above first.")

            logger.info("user %s message on conversation %s: %s", user_id, conversation.id, text)
            await self._db.log_message(conversation.id, "user", text)
            history = await self._load_history(conversation.id)
            result = await self._agent.run(text, message_history=history)
            return await self._finish(conversation.id, result)

    async def discard(self, user_id: int) -> None:
        """Denies any pending tool-call approvals on the user's open conversation and closes it"""
        async with self._lock_for(user_id):
            conversation = await self._db.get_open_conversation(user_id)
            if conversation is not None:
                logger.info("user %s discarding conversation %s", user_id, conversation.id)
                await self._db.deny_pending_tool_calls(conversation.id)
                await self._db.close_conversation(conversation.id)

    async def resolve_approval(
        self, user_id: int, row_id: int, approved: bool
    ) -> tuple[str, dict, TurnResult | None]:
        """Records the decision and, once every pending call in the batch is
        decided, resumes the agent run.

        Returns (tool_name, args, TurnResult): TurnResult is None while sibling
        approvals in the same batch are still pending.
        """
        async with self._lock_for(user_id):
            call_row = await self._db.get_tool_call(row_id)
            if call_row is None or call_row.status != "pending":
                raise ValueError("This request is no longer pending.")

            conversation = await self._db.get_open_conversation(user_id)
            if conversation is None or conversation.id != call_row.conversation_id:
                raise ValueError("This request belongs to a different conversation.")

            await self._db.resolve_tool_call(row_id, "approved" if approved else "denied")
            logger.info(
                "user %s %s tool call row %s (%s)",
                user_id,
                "approved" if approved else "denied",
                row_id,
                call_row.tool_name,
            )

            turn_result = None
            if await self._db.count_pending_tool_calls(conversation.id) == 0:
                turn_result = await self._resume(conversation.id)

            return call_row.tool_name, json.loads(call_row.args_json), turn_result

    async def _resume(self, conversation_id: int) -> TurnResult:
        decided = await self._db.get_unconsumed_decided_tool_calls(conversation_id)
        results = DeferredToolResults()
        for row in decided:
            results.approvals[row.tool_call_id] = (
                True if row.status == "approved" else ToolDenied("The user denied this action.")
            )

        logger.info("conversation %s resuming with %s decided tool call(s)", conversation_id, len(decided))
        history = await self._load_history(conversation_id)
        result = await self._agent.run(message_history=history, deferred_tool_results=results)

        result_by_call_id = {
            part.tool_call_id: part.content
            for message in result.new_messages()
            for part in getattr(message, "parts", [])
            if isinstance(part, ToolReturnPart)
        }
        for row in decided:
            if row.tool_call_id in result_by_call_id:
                logger.info("tool call row %s result: %s", row.id, result_by_call_id[row.tool_call_id])
                await self._db.set_tool_call_result(row.id, result_by_call_id[row.tool_call_id])
        await self._db.mark_tool_calls_consumed([row.id for row in decided])

        return await self._finish(
            conversation_id, result, exclude_auto_call_ids=frozenset(row.tool_call_id for row in decided)
        )
