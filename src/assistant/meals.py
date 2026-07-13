import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.messages import BinaryContent

from . import i18n
from .db import Database, UserSettings
from .nutrition import NutritionFacts, resolve_reference_profile

logger = logging.getLogger(__name__)

DAY_SECONDS = 24 * 3600
WEEK_SECONDS = 7 * DAY_SECONDS

# Serving-level macro fields summed for /day_summary and /week_summary.
MACRO_SERVING_FIELDS = (
    "energy_kcal_serving",
    "protein_g_serving",
    "fat_g_serving",
    "saturated_fat_g_serving",
    "carbohydrate_g_serving",
    "sugars_g_serving",
    "sodium_mg_serving",
)


@dataclass
class NutrientHighlight:
    nutrient_key: str  # e.g. "vitamin_c_mg" - resolved to a label at render time via i18n.nutrient_label
    pct_daily_value: float
    tier: str  # "excellent" (>=20% DV) | "good" (10-19% DV)


@dataclass
class MealLogResult:
    facts: NutritionFacts | None = None
    highlights: list[NutrientHighlight] = field(default_factory=list)
    error: str | None = None


@dataclass
class DaySummary:
    since: float
    totals: dict[str, float]  # serving-level macro sums, keyed like NutritionFacts fields
    meal_count: int


@dataclass
class WeekSummary:
    this_week_daily_avg: dict[str, float]  # macros
    prior_week_daily_avg: dict[str, float] | None  # None => "no prior data"
    weekly_norm_coverage: dict[str, float]  # nutrient -> % of (7 x daily RDI) covered


def _time_of_day_label(local_hour: int) -> str:
    if 5 <= local_hour < 11:
        return "Breakfast"
    if 11 <= local_hour < 15:
        return "Lunch"
    if 17 <= local_hour < 22:
        return "Dinner"
    return "Snack"


def _with_context(content: str | list, lang: str, local_dt: datetime) -> str | list:
    """Appends a context directive to the nutrition-agent prompt: the user's local
    wall-clock time (never the timezone name/offset itself, only the resolved
    time) and, for non-English users, the reply language.
    """
    directive = f"Current local time: {local_dt:%Y-%m-%d %H:%M}."
    if lang != "en":
        language_name = i18n.LANGUAGE_NAMES[lang]
        directive += f" Respond in {language_name}: write food_description and serving_description in {language_name}."

    if isinstance(content, str):
        return f"{content}\n\n{directive}"
    content = list(content)
    content[0] = f"{content[0]}\n\n{directive}"
    return content


class MealService:
    """Logs meals via a one-shot nutrition agent and reports totals, parallel to
    `ConversationService` but talking to `db.py` directly - it never opens a
    `conversations` row or touches the kept-but-unwired approval machinery.
    """

    def __init__(self, db: Database, nutrition_agent: Agent):
        self._db = db
        self._agent = nutrition_agent

    async def _highlights_for(self, facts: NutritionFacts, sex: str | None, age: int | None) -> list[NutrientHighlight]:
        profile = resolve_reference_profile(sex, age)
        highlights = []
        for nutrient, reference_value in profile.items():
            value = getattr(facts, nutrient, None)
            if value is None:
                continue
            pct = value / reference_value * 100
            if pct < 10:
                continue
            tier = "excellent" if pct >= 20 else "good"
            highlights.append(NutrientHighlight(nutrient_key=nutrient, pct_daily_value=pct, tier=tier))
        return highlights

    async def _log(self, user_id: int, content: str | list) -> MealLogResult:
        settings = await self._db.get_or_create_user_settings(user_id)
        now = time.time()
        local_dt = datetime.fromtimestamp(now, tz=ZoneInfo(settings.timezone))
        content = _with_context(content, settings.language, local_dt)

        try:
            result = await self._agent.run(content)
        except UnexpectedModelBehavior as exc:
            logger.info("user %s nutrition analysis failed: %s", user_id, exc)
            return MealLogResult(error=f"Nutrition analysis failed: {exc}")

        facts = result.output
        name = f"{_time_of_day_label(local_dt.hour)}: {facts.food_description}"

        await self._db.insert_meal(user_id, now, name, **facts.model_dump(exclude={"food_description"}))
        logger.info("user %s logged meal: %s", user_id, name)

        highlights = await self._highlights_for(facts, settings.sex, settings.age)
        return MealLogResult(facts=facts, highlights=highlights)

    async def log_text(self, user_id: int, text: str) -> MealLogResult:
        return await self._log(user_id, text)

    async def log_photo(
        self, user_id: int, image_bytes: bytes, media_type: str, caption: str | None
    ) -> MealLogResult:
        text = caption or "Identify this food and estimate its nutrition facts."
        return await self._log(user_id, [text, BinaryContent(data=image_bytes, media_type=media_type)])

    async def resolve_language(self, user_id: int, language_code: str | None) -> str:
        lang = i18n.resolve_language(language_code)
        await self._db.set_language(user_id, lang)
        return lang

    async def day_summary(self, user_id: int) -> DaySummary:
        now = time.time()
        settings = await self._db.get_or_create_user_settings(user_id)
        last = settings.last_day_summary_at
        since = last if last is not None and (now - last) <= 36 * 3600 else now - DAY_SECONDS

        rows = await self._db.get_meals_between(user_id, since, now)
        totals = {field_name: 0.0 for field_name in MACRO_SERVING_FIELDS}
        for row in rows:
            for field_name in MACRO_SERVING_FIELDS:
                totals[field_name] += getattr(row, field_name)

        await self._db.set_last_day_summary_at(user_id, now)
        return DaySummary(since=since, totals=totals, meal_count=len(rows))

    async def week_summary(self, user_id: int) -> WeekSummary:
        now = time.time()
        this_rows = await self._db.get_meals_between(user_id, now - WEEK_SECONDS, now)
        prior_rows = await self._db.get_meals_between(user_id, now - 2 * WEEK_SECONDS, now - WEEK_SECONDS)

        this_avg = {
            field_name: sum(getattr(row, field_name) for row in this_rows) / 7
            for field_name in MACRO_SERVING_FIELDS
        }
        prior_avg = (
            {
                field_name: sum(getattr(row, field_name) for row in prior_rows) / 7
                for field_name in MACRO_SERVING_FIELDS
            }
            if prior_rows
            else None
        )

        settings = await self._db.get_or_create_user_settings(user_id)
        profile = resolve_reference_profile(settings.sex, settings.age)
        coverage = {
            nutrient: sum(getattr(row, nutrient) or 0 for row in this_rows) / (7 * reference_value) * 100
            for nutrient, reference_value in profile.items()
        }

        return WeekSummary(this_week_daily_avg=this_avg, prior_week_daily_avg=prior_avg, weekly_norm_coverage=coverage)

    async def destroy(self, user_id: int) -> None:
        await self._db.delete_user_meals(user_id)
        await self._db.reset_user_settings(user_id)
        logger.info("user %s destroyed nutrition data", user_id)

    async def set_timezone(self, user_id: int, tz_name: str) -> None:
        await self._db.set_timezone(user_id, tz_name)

    async def set_profile(self, user_id: int, sex: str, age: int) -> None:
        await self._db.set_profile(user_id, sex, age)

    async def get_settings(self, user_id: int) -> UserSettings:
        return await self._db.get_or_create_user_settings(user_id)
