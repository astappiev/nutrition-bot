import json
import time
from dataclasses import dataclass

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    closed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_conversations_user_open
    ON conversations (user_id) WHERE closed_at IS NULL;

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations (id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id);

CREATE TABLE IF NOT EXISTS agent_state (
    conversation_id INTEGER PRIMARY KEY REFERENCES conversations (id),
    history_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations (id),
    tool_call_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    args_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result_json TEXT,
    created_at REAL NOT NULL,
    resolved_at REAL,
    consumed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_tool_calls_conversation ON tool_calls (conversation_id);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    last_day_summary_at REAL,
    sex TEXT,
    age INTEGER
);

CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    logged_at REAL NOT NULL,
    name TEXT NOT NULL,
    serving_description TEXT NOT NULL,
    serving_grams REAL NOT NULL,
    energy_kcal_serving REAL NOT NULL,
    energy_kcal_100g REAL NOT NULL,
    protein_g_serving REAL NOT NULL,
    protein_g_100g REAL NOT NULL,
    fat_g_serving REAL NOT NULL,
    fat_g_100g REAL NOT NULL,
    saturated_fat_g_serving REAL NOT NULL,
    saturated_fat_g_100g REAL NOT NULL,
    carbohydrate_g_serving REAL NOT NULL,
    carbohydrate_g_100g REAL NOT NULL,
    sugars_g_serving REAL NOT NULL,
    sugars_g_100g REAL NOT NULL,
    sodium_mg_serving REAL NOT NULL,
    sodium_mg_100g REAL NOT NULL,
    vitamin_a_mcg REAL, beta_carotene_mcg REAL, vitamin_d_mcg REAL, vitamin_e_mg REAL,
    vitamin_k_mcg REAL, vitamin_b1_mg REAL, vitamin_b2_mg REAL, niacin_mg REAL,
    vitamin_b6_mg REAL, folate_mcg REAL, pantothenic_acid_mg REAL, biotin_mcg REAL,
    vitamin_b12_mcg REAL, vitamin_c_mg REAL,
    chloride_mg REAL, potassium_mg REAL, calcium_mg REAL, phosphorus_mg REAL,
    magnesium_mg REAL, iron_mg REAL, iodine_mcg REAL, fluoride_mg REAL, zinc_mg REAL,
    selenium_mcg REAL, copper_mg REAL, manganese_mg REAL, chromium_mcg REAL,
    molybdenum_mcg REAL, boron_mg REAL, silicon_mg REAL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_meals_user_time ON meals (user_id, logged_at);
"""

# Vitamin/mineral columns, serving-level only - shared by the meals table and
# NutritionFacts (nutrition.py) so a meal row and a model estimate line up field-for-field.
VITAMIN_MINERAL_COLUMNS = (
    "vitamin_a_mcg", "beta_carotene_mcg", "vitamin_d_mcg", "vitamin_e_mg",
    "vitamin_k_mcg", "vitamin_b1_mg", "vitamin_b2_mg", "niacin_mg",
    "vitamin_b6_mg", "folate_mcg", "pantothenic_acid_mg", "biotin_mcg",
    "vitamin_b12_mcg", "vitamin_c_mg",
    "chloride_mg", "potassium_mg", "calcium_mg", "phosphorus_mg",
    "magnesium_mg", "iron_mg", "iodine_mcg", "fluoride_mg", "zinc_mg",
    "selenium_mcg", "copper_mg", "manganese_mg", "chromium_mcg",
    "molybdenum_mcg", "boron_mg", "silicon_mg",
)

MEAL_COLUMNS = (
    "id", "user_id", "logged_at", "name", "serving_description", "serving_grams",
    "energy_kcal_serving", "energy_kcal_100g",
    "protein_g_serving", "protein_g_100g",
    "fat_g_serving", "fat_g_100g",
    "saturated_fat_g_serving", "saturated_fat_g_100g",
    "carbohydrate_g_serving", "carbohydrate_g_100g",
    "sugars_g_serving", "sugars_g_100g",
    "sodium_mg_serving", "sodium_mg_100g",
    *VITAMIN_MINERAL_COLUMNS,
    "created_at",
)


@dataclass
class Conversation:
    id: int
    user_id: int


@dataclass
class UserSettings:
    user_id: int
    timezone: str
    last_day_summary_at: float | None
    sex: str | None
    age: int | None


@dataclass
class MealRow:
    id: int
    user_id: int
    logged_at: float
    name: str
    serving_description: str
    serving_grams: float
    energy_kcal_serving: float
    energy_kcal_100g: float
    protein_g_serving: float
    protein_g_100g: float
    fat_g_serving: float
    fat_g_100g: float
    saturated_fat_g_serving: float
    saturated_fat_g_100g: float
    carbohydrate_g_serving: float
    carbohydrate_g_100g: float
    sugars_g_serving: float
    sugars_g_100g: float
    sodium_mg_serving: float
    sodium_mg_100g: float
    vitamin_a_mcg: float | None
    beta_carotene_mcg: float | None
    vitamin_d_mcg: float | None
    vitamin_e_mg: float | None
    vitamin_k_mcg: float | None
    vitamin_b1_mg: float | None
    vitamin_b2_mg: float | None
    niacin_mg: float | None
    vitamin_b6_mg: float | None
    folate_mcg: float | None
    pantothenic_acid_mg: float | None
    biotin_mcg: float | None
    vitamin_b12_mcg: float | None
    vitamin_c_mg: float | None
    chloride_mg: float | None
    potassium_mg: float | None
    calcium_mg: float | None
    phosphorus_mg: float | None
    magnesium_mg: float | None
    iron_mg: float | None
    iodine_mcg: float | None
    fluoride_mg: float | None
    zinc_mg: float | None
    selenium_mcg: float | None
    copper_mg: float | None
    manganese_mg: float | None
    chromium_mcg: float | None
    molybdenum_mcg: float | None
    boron_mg: float | None
    silicon_mg: float | None
    created_at: float


@dataclass
class ToolCallRow:
    id: int
    conversation_id: int
    tool_call_id: str
    tool_name: str
    args_json: str
    status: str


class Database:
    def __init__(self, path: str):
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        assert self._conn is not None, "Database.connect() was not called"
        return self._conn

    async def get_open_conversation(self, user_id: int) -> Conversation | None:
        cursor = await self.conn.execute(
            "SELECT id, user_id FROM conversations WHERE user_id = ? AND closed_at IS NULL",
            (user_id,),
        )
        row = await cursor.fetchone()
        return Conversation(id=row[0], user_id=row[1]) if row else None

    async def open_conversation(self, user_id: int) -> Conversation:
        cursor = await self.conn.execute(
            "INSERT INTO conversations (user_id, created_at) VALUES (?, ?)",
            (user_id, time.time()),
        )
        await self.conn.commit()
        return Conversation(id=cursor.lastrowid, user_id=user_id)

    async def close_conversation(self, conversation_id: int) -> None:
        await self.conn.execute(
            "UPDATE conversations SET closed_at = ? WHERE id = ?",
            (time.time(), conversation_id),
        )
        await self.conn.commit()

    async def get_or_open_conversation(self, user_id: int) -> Conversation:
        existing = await self.get_open_conversation(user_id)
        return existing if existing is not None else await self.open_conversation(user_id)

    async def log_message(self, conversation_id: int, role: str, content: str) -> None:
        await self.conn.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, time.time()),
        )
        await self.conn.commit()

    async def load_history_json(self, conversation_id: int) -> str | None:
        cursor = await self.conn.execute(
            "SELECT history_json FROM agent_state WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def save_history_json(self, conversation_id: int, history_json: str) -> None:
        await self.conn.execute(
            """INSERT INTO agent_state (conversation_id, history_json) VALUES (?, ?)
               ON CONFLICT (conversation_id) DO UPDATE SET history_json = excluded.history_json""",
            (conversation_id, history_json),
        )
        await self.conn.commit()

    async def create_tool_call(
        self, conversation_id: int, tool_call_id: str, tool_name: str, args: object
    ) -> int:
        cursor = await self.conn.execute(
            """INSERT INTO tool_calls (conversation_id, tool_call_id, tool_name, args_json, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (conversation_id, tool_call_id, tool_name, json.dumps(args), time.time()),
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_tool_call(self, row_id: int) -> ToolCallRow | None:
        cursor = await self.conn.execute(
            "SELECT id, conversation_id, tool_call_id, tool_name, args_json, status FROM tool_calls WHERE id = ?",
            (row_id,),
        )
        row = await cursor.fetchone()
        return ToolCallRow(*row) if row else None

    async def resolve_tool_call(self, row_id: int, status: str, result: object = None) -> None:
        await self.conn.execute(
            "UPDATE tool_calls SET status = ?, result_json = ?, resolved_at = ? WHERE id = ?",
            (status, json.dumps(result) if result is not None else None, time.time(), row_id),
        )
        await self.conn.commit()

    async def deny_pending_tool_calls(self, conversation_id: int) -> None:
        await self.conn.execute(
            "UPDATE tool_calls SET status = 'denied', resolved_at = ? WHERE conversation_id = ? AND status = 'pending'",
            (time.time(), conversation_id),
        )
        await self.conn.commit()

    async def count_pending_tool_calls(self, conversation_id: int) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) FROM tool_calls WHERE conversation_id = ? AND status = 'pending'",
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return row[0]

    async def get_unconsumed_decided_tool_calls(self, conversation_id: int) -> list[ToolCallRow]:
        cursor = await self.conn.execute(
            """SELECT id, conversation_id, tool_call_id, tool_name, args_json, status FROM tool_calls
               WHERE conversation_id = ? AND status != 'pending' AND consumed_at IS NULL""",
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        return [ToolCallRow(*row) for row in rows]

    async def mark_tool_calls_consumed(self, row_ids: list[int]) -> None:
        if not row_ids:
            return
        placeholders = ",".join("?" for _ in row_ids)
        await self.conn.execute(
            f"UPDATE tool_calls SET consumed_at = ? WHERE id IN ({placeholders})",
            (time.time(), *row_ids),
        )
        await self.conn.commit()

    async def set_tool_call_result(self, row_id: int, result: object) -> None:
        await self.conn.execute(
            "UPDATE tool_calls SET result_json = ? WHERE id = ?",
            (json.dumps(result), row_id),
        )
        await self.conn.commit()

    async def get_or_create_user_settings(self, user_id: int) -> UserSettings:
        cursor = await self.conn.execute(
            "SELECT user_id, timezone, last_day_summary_at, sex, age FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is not None:
            return UserSettings(*row)

        await self.conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
        await self.conn.commit()
        return UserSettings(user_id=user_id, timezone="UTC", last_day_summary_at=None, sex=None, age=None)

    async def set_timezone(self, user_id: int, tz_name: str) -> None:
        await self.conn.execute(
            """INSERT INTO user_settings (user_id, timezone) VALUES (?, ?)
               ON CONFLICT (user_id) DO UPDATE SET timezone = excluded.timezone""",
            (user_id, tz_name),
        )
        await self.conn.commit()

    async def set_profile(self, user_id: int, sex: str, age: int) -> None:
        await self.conn.execute(
            """INSERT INTO user_settings (user_id, sex, age) VALUES (?, ?, ?)
               ON CONFLICT (user_id) DO UPDATE SET sex = excluded.sex, age = excluded.age""",
            (user_id, sex, age),
        )
        await self.conn.commit()

    async def set_last_day_summary_at(self, user_id: int, ts: float) -> None:
        await self.conn.execute(
            """INSERT INTO user_settings (user_id, last_day_summary_at) VALUES (?, ?)
               ON CONFLICT (user_id) DO UPDATE SET last_day_summary_at = excluded.last_day_summary_at""",
            (user_id, ts),
        )
        await self.conn.commit()

    async def insert_meal(self, user_id: int, logged_at: float, name: str, **facts_fields: object) -> int:
        columns = ["user_id", "logged_at", "name", *facts_fields.keys(), "created_at"]
        placeholders = ", ".join("?" for _ in columns)
        values = [user_id, logged_at, name, *facts_fields.values(), time.time()]
        cursor = await self.conn.execute(
            f"INSERT INTO meals ({', '.join(columns)}) VALUES ({placeholders})", values
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_meals_between(self, user_id: int, start: float, end: float) -> list[MealRow]:
        cursor = await self.conn.execute(
            f"SELECT {', '.join(MEAL_COLUMNS)} FROM meals "
            "WHERE user_id = ? AND logged_at >= ? AND logged_at < ? ORDER BY logged_at",
            (user_id, start, end),
        )
        rows = await cursor.fetchall()
        return [MealRow(*row) for row in rows]

    async def delete_user_meals(self, user_id: int) -> None:
        await self.conn.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def reset_user_settings(self, user_id: int) -> None:
        await self.conn.execute(
            "UPDATE user_settings SET timezone = 'UTC', last_day_summary_at = NULL, sex = NULL, age = NULL "
            "WHERE user_id = ?",
            (user_id,),
        )
        await self.conn.commit()
