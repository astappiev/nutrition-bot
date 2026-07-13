from pydantic_ai import Agent, DeferredToolRequests, RunContext
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.tools import ToolDefinition

from .config import Settings


def _needs_approval(auto_approved: frozenset[str]):
    def check(ctx: RunContext, tool_def: ToolDefinition, tool_args: dict) -> bool:
        return tool_def.name not in auto_approved

    return check


def build_agent(settings: Settings) -> Agent:
    auto_approved = frozenset(settings.auto_approve_tools)
    toolsets = [
        MCPToolset(server.url, headers=server.headers or None).approval_required(_needs_approval(auto_approved))
        for server in settings.mcp_servers
    ]
    return Agent(
        settings.llm_model,
        toolsets=toolsets,
        output_type=[str, DeferredToolRequests],
        instructions=(
            "You are a helpful personal assistant reachable over Telegram. "
            "Call tools directly whenever they help answer the request - do not ask "
            "the user for permission or confirmation in chat first. The system "
            "automatically pauses every tool call and shows the user a Telegram "
            "Approve/Deny prompt before it runs, so a separate confirmation from "
            "you would be redundant and slow things down."
        ),
    )
