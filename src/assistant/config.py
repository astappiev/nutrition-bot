import json
from typing import Annotated

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class McpServerConfig(BaseModel):
    url: str
    headers: dict[str, str] = Field(default_factory=dict)


class Settings(BaseSettings):
    # extra="ignore": .env may carry provider API keys (GEMINI_API_KEY, etc.)
    # that aren't Settings fields - they're read directly by the model
    # provider via os.environ, populated below by load_dotenv().
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str
    allowed_user_ids: Annotated[list[int], NoDecode]
    llm_model: str = "google:gemini-3.1-flash-lite"
    mcp_servers: Annotated[list[McpServerConfig], NoDecode] = Field(default_factory=list)
    auto_approve_tools: Annotated[list[str], NoDecode] = Field(default_factory=list)
    database_path: str = "nutrition.db"
    log_level: str = "INFO"

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def _split_csv_ints(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("auto_approve_tools", mode="before")
    @classmethod
    def _split_csv_strs(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("mcp_servers", mode="before")
    @classmethod
    def _parse_mcp_servers(cls, value: object) -> object:
        """MCP_SERVERS accepts either a JSON array of {"url", "headers"}
        objects (for servers that need auth headers), or a plain
        comma-separated list of URLs for servers that need none."""
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            return json.loads(value)
        return [{"url": url.strip()} for url in value.split(",") if url.strip()]

    def is_user_allowed(self, user_id: int) -> bool:
        return user_id in self.allowed_user_ids


def load_settings() -> Settings:
    # Populate the real process environment (not just this Settings object) so
    # provider SDKs that read their API key via os.getenv (e.g. GoogleProvider
    # reading GEMINI_API_KEY) see it too.
    load_dotenv()
    return Settings()
