from pydantic import BaseModel
from pydantic_ai import Agent

from .config import Settings


class NutritionFacts(BaseModel):
    food_description: str
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

    # Vitamins/minerals: serving-level only (no _100g pair), all optional - the
    # model should omit a field rather than guess when it has no basis to estimate it.
    vitamin_a_mcg: float | None = None
    beta_carotene_mcg: float | None = None
    vitamin_d_mcg: float | None = None
    vitamin_e_mg: float | None = None
    vitamin_k_mcg: float | None = None
    vitamin_b1_mg: float | None = None
    vitamin_b2_mg: float | None = None
    niacin_mg: float | None = None
    vitamin_b6_mg: float | None = None
    folate_mcg: float | None = None
    pantothenic_acid_mg: float | None = None
    biotin_mcg: float | None = None
    vitamin_b12_mcg: float | None = None
    vitamin_c_mg: float | None = None
    chloride_mg: float | None = None
    potassium_mg: float | None = None
    calcium_mg: float | None = None
    phosphorus_mg: float | None = None
    magnesium_mg: float | None = None
    iron_mg: float | None = None
    iodine_mcg: float | None = None
    fluoride_mg: float | None = None
    zinc_mg: float | None = None
    selenium_mcg: float | None = None
    copper_mg: float | None = None
    manganese_mg: float | None = None
    chromium_mcg: float | None = None
    molybdenum_mcg: float | None = None
    boron_mg: float | None = None
    silicon_mg: float | None = None


def build_nutrition_agent(settings: Settings) -> Agent:
    """A minimal, history-free agent dedicated to meal logging.

    Same shape as the deleted `build_image_agent`: no tools, no history, no
    approval gating - each call is a single isolated prompt -> facts round trip,
    reused directly for both text and photo input via `Agent.run`'s
    `Sequence[UserContent]` support.
    """
    return Agent(
        settings.llm_model,
        output_type=NutritionFacts,
        instructions=(
            "Estimate nutrition facts for the described or pictured food, including "
            "whichever vitamins and minerals you can reasonably infer are present in "
            "meaningful amounts (e.g. citrus -> vitamin C, red meat -> iron/zinc/B12, "
            "dairy -> calcium). Leave a vitamin/mineral field unset rather than "
            "guessing when there's no basis to estimate it. Always give a generous "
            "best-effort serving-size estimate rather than asking clarifying questions."
        ),
    )


# nutrient key -> daily reference amount, same unit as the matching NutritionFacts field.
# Approximate, sourced from standard NIH ODS / FDA tables - not medical advice, just a
# reasonableness yardstick for callouts and weekly coverage math.
NutrientTable = dict[str, float]

REFERENCE_PROFILES: dict[str, NutrientTable] = {
    "default": {  # generic adult, used when sex/age is unset
        "vitamin_a_mcg": 900, "vitamin_c_mg": 90, "vitamin_d_mcg": 20, "vitamin_e_mg": 15,
        "vitamin_k_mcg": 120, "vitamin_b1_mg": 1.2, "vitamin_b2_mg": 1.3, "niacin_mg": 16,
        "vitamin_b6_mg": 1.7, "folate_mcg": 400, "vitamin_b12_mcg": 2.4, "biotin_mcg": 30,
        "pantothenic_acid_mg": 5, "calcium_mg": 1300, "iron_mg": 18, "phosphorus_mg": 1250,
        "iodine_mcg": 150, "magnesium_mg": 420, "zinc_mg": 11, "selenium_mcg": 55,
        "copper_mg": 0.9, "manganese_mg": 2.3, "chromium_mcg": 35, "molybdenum_mcg": 45,
        "chloride_mg": 2300, "potassium_mg": 4700, "fluoride_mg": 4,
    },
}

# Only the handful of nutrients that actually shift by sex/age; everything else
# (folate, B12, biotin, phosphorus, iodine, selenium, copper, molybdenum, fluoride, etc.)
# stays flat across adult groups and is inherited from "default" below.
REFERENCE_PROFILES["male:19-50"] = {
    **REFERENCE_PROFILES["default"],
    "iron_mg": 8, "calcium_mg": 1000, "magnesium_mg": 400, "zinc_mg": 11,
    "chromium_mcg": 35, "vitamin_d_mcg": 15, "vitamin_b6_mg": 1.3,
    "potassium_mg": 3400, "chloride_mg": 2300, "manganese_mg": 2.3,
}
REFERENCE_PROFILES["male:51+"] = {
    **REFERENCE_PROFILES["default"],
    "iron_mg": 8, "calcium_mg": 1000, "magnesium_mg": 420, "zinc_mg": 11,
    "chromium_mcg": 30, "vitamin_d_mcg": 20, "vitamin_b6_mg": 1.7,
    "potassium_mg": 3400, "chloride_mg": 2000, "manganese_mg": 2.3,
}
REFERENCE_PROFILES["female:19-50"] = {
    **REFERENCE_PROFILES["default"],
    "iron_mg": 18, "calcium_mg": 1000, "magnesium_mg": 310, "zinc_mg": 8,
    "chromium_mcg": 25, "vitamin_d_mcg": 15, "vitamin_b6_mg": 1.3,
    "potassium_mg": 2600, "chloride_mg": 2300, "manganese_mg": 1.8,
}
REFERENCE_PROFILES["female:51+"] = {
    **REFERENCE_PROFILES["default"],
    "iron_mg": 8, "calcium_mg": 1200, "magnesium_mg": 320, "zinc_mg": 8,
    "chromium_mcg": 20, "vitamin_d_mcg": 20, "vitamin_b6_mg": 1.5,
    "potassium_mg": 2600, "chloride_mg": 2000, "manganese_mg": 1.8,
}

# beta_carotene_mcg, boron_mg, silicon_mg have no FDA/NIH-established reference value -
# they're tracked and shown as raw amounts when the model estimates them, but excluded
# from %DV callouts and weekly coverage math (no denominator to divide by).


def resolve_reference_profile(sex: str | None, age: int | None) -> NutrientTable:
    if sex not in ("male", "female") or age is None:
        return REFERENCE_PROFILES["default"]
    bucket = "19-50" if age < 51 else "51+"
    return REFERENCE_PROFILES[f"{sex}:{bucket}"]
