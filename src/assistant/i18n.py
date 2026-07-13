SUPPORTED_LANGUAGES = ("en", "de", "uk")
DEFAULT_LANGUAGE = "en"

# Used in the language directive appended to nutrition-agent prompts (meals.py),
# so the model knows what to call the target language in its own instructions.
LANGUAGE_NAMES = {"en": "English", "de": "German", "uk": "Ukrainian"}


def resolve_language(telegram_code: str | None) -> str:
    """Map a Telegram `User.language_code` (e.g. "de-DE", "uk") to a supported
    language, falling back to English for anything we don't have a catalog for.
    """
    if not telegram_code:
        return DEFAULT_LANGUAGE
    base = telegram_code.split("-")[0].lower()
    return base if base in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


STRINGS: dict[str, dict[str, str]] = {
    "help_text": {
        "en": (
            "Hi! I'm Nutrition Couch. Send me a food photo or describe what you ate, any time of "
            "day, and I'll estimate its nutrition facts and log it.\n\n"
            "Commands:\n"
            "/profile <male|female> <age> - set your profile for personalized nutrient targets\n"
            "/timezone <IANA name> - set your timezone, e.g. Europe/Berlin\n"
            "/day_summary - totals for the last day\n"
            "/week_summary - this week vs last week, plus nutrient coverage\n"
            "/destroy - delete all your logged data"
        ),
        "de": (
            "Hallo! Ich bin Nutrition Couch. Schick mir ein Foto deines Essens oder beschreibe, was "
            "du gegessen hast, egal zu welcher Tageszeit, und ich schätze die Nährwerte und "
            "protokolliere sie.\n\n"
            "Befehle:\n"
            "/profile <male|female> <age> - Profil für personalisierte Nährstoffziele festlegen\n"
            "/timezone <IANA-Name> - Zeitzone festlegen, z. B. Europe/Berlin\n"
            "/day_summary - Summen für den letzten Tag\n"
            "/week_summary - diese Woche vs. letzte Woche, plus Nährstoffabdeckung\n"
            "/destroy - alle protokollierten Daten löschen"
        ),
        "uk": (
            "Привіт! Я Nutrition Couch. Надішли фото їжі або опиши, що ти з'їв(ла), у будь-який час "
            "доби, і я оціню харчову цінність та запишу її.\n\n"
            "Команди:\n"
            "/profile <male|female> <age> - встановити профіль для персональних норм нутрієнтів\n"
            "/timezone <IANA назва> - встановити часовий пояс, напр. Europe/Berlin\n"
            "/day_summary - підсумок за останню добу\n"
            "/week_summary - цей тиждень проти минулого, плюс покриття нутрієнтів\n"
            "/destroy - видалити всі записані дані"
        ),
    },
    "profile_nudge": {
        "en": "\n\nSet your profile for personalized nutrient targets: /profile <male|female> <age>",
        "de": "\n\nLege dein Profil für personalisierte Nährstoffziele fest: /profile <male|female> <age>",
        "uk": "\n\nВстанови свій профіль для персональних норм нутрієнтів: /profile <male|female> <age>",
    },
    "timezone_usage": {
        "en": "Usage: /timezone <IANA name>\nExample: /timezone Europe/Berlin",
        "de": "Verwendung: /timezone <IANA-Name>\nBeispiel: /timezone Europe/Berlin",
        "uk": "Використання: /timezone <IANA назва>\nПриклад: /timezone Europe/Berlin",
    },
    "timezone_unknown": {
        "en": "Unknown timezone: {tz}",
        "de": "Unbekannte Zeitzone: {tz}",
        "uk": "Невідомий часовий пояс: {tz}",
    },
    "timezone_set": {
        "en": "Timezone set to {tz}.",
        "de": "Zeitzone auf {tz} gesetzt.",
        "uk": "Часовий пояс встановлено: {tz}.",
    },
    "profile_usage": {
        "en": "Usage: /profile <male|female> <age>\nExample: /profile female 29",
        "de": "Verwendung: /profile <male|female> <age>\nBeispiel: /profile female 29",
        "uk": "Використання: /profile <male|female> <age>\nПриклад: /profile female 29",
    },
    "profile_set": {
        "en": "Profile set: {sex}, age {age}.",
        "de": "Profil gespeichert: {sex}, Alter {age}.",
        "uk": "Профіль збережено: {sex}, вік {age}.",
    },
    "day_summary_empty": {
        "en": "No meals logged since the last summary.",
        "de": "Seit der letzten Zusammenfassung wurden keine Mahlzeiten protokolliert.",
        "uk": "З моменту останнього підсумку прийомів їжі не записано.",
    },
    "meals_logged": {
        "en": "Meals logged: {count}",
        "de": "Protokollierte Mahlzeiten: {count}",
        "uk": "Записано прийомів їжі: {count}",
    },
    "week_daily_avg_header": {
        "en": "Daily average (this week):",
        "de": "Täglicher Durchschnitt (diese Woche):",
        "uk": "Середнє за день (цей тиждень):",
    },
    "week_delta_suffix": {
        "en": " ({sign}{delta} vs last week)",
        "de": " ({sign}{delta} ggü. letzter Woche)",
        "uk": " ({sign}{delta} проти минулого тижня)",
    },
    "week_no_prior_data": {
        "en": "(No data from the prior week to compare against.)",
        "de": "(Keine Daten der Vorwoche zum Vergleich vorhanden.)",
        "uk": "(Даних за минулий тиждень для порівняння немає.)",
    },
    "week_coverage_header": {
        "en": "Weekly nutrient coverage (% of reference intake):",
        "de": "Wöchentliche Nährstoffabdeckung (% der Referenzmenge):",
        "uk": "Тижневе покриття нутрієнтів (% від норми):",
    },
    "week_coverage_line": {
        "en": "{nutrient}: {pct}% of weekly target",
        "de": "{nutrient}: {pct}% des Wochenziels",
        "uk": "{nutrient}: {pct}% від тижневої норми",
    },
    "destroy_confirm": {
        "en": "This will permanently delete all your logged meals and reset your profile/timezone. Continue?",
        "de": (
            "Dadurch werden alle protokollierten Mahlzeiten dauerhaft gelöscht und dein "
            "Profil/deine Zeitzone zurückgesetzt. Fortfahren?"
        ),
        "uk": "Це остаточно видалить усі записані прийоми їжі та скине твій профіль/часовий пояс. Продовжити?",
    },
    "destroy_yes": {
        "en": "Yes, delete everything",
        "de": "Ja, alles löschen",
        "uk": "Так, видалити все",
    },
    "destroy_cancel": {
        "en": "Cancel",
        "de": "Abbrechen",
        "uk": "Скасувати",
    },
    "destroy_cancelled": {
        "en": "Cancelled. Your data is safe.",
        "de": "Abgebrochen. Deine Daten sind sicher.",
        "uk": "Скасовано. Твої дані в безпеці.",
    },
    "destroy_not_yours": {
        "en": "This confirmation isn't yours.",
        "de": "Diese Bestätigung ist nicht für dich.",
        "uk": "Це підтвердження не для тебе.",
    },
    "destroy_done": {
        "en": "All your nutrition data has been deleted.",
        "de": "Alle deine Ernährungsdaten wurden gelöscht.",
        "uk": "Усі твої дані про харчування видалено.",
    },
    "clear_cleared": {
        "en": "Conversation cleared.",
        "de": "Unterhaltung zurückgesetzt.",
        "uk": "Розмову очищено.",
    },
    "generic_error": {
        "en": "Something went wrong handling that. Please try again.",
        "de": "Dabei ist etwas schiefgelaufen. Bitte versuch es erneut.",
        "uk": "Щось пішло не так. Спробуй ще раз.",
    },
    "meal_analysis_error": {
        "en": "Something went wrong analyzing that.",
        "de": "Bei der Analyse ist etwas schiefgelaufen.",
        "uk": "Під час аналізу щось пішло не так.",
    },
    "meal_serving": {
        "en": "Serving: {desc} ({grams} g)",
        "de": "Portion: {desc} ({grams} g)",
        "uk": "Порція: {desc} ({grams} г)",
    },
    "meal_energy": {
        "en": "Energy: {kcal} kcal",
        "de": "Energie: {kcal} kcal",
        "uk": "Енергія: {kcal} ккал",
    },
    "meal_protein": {
        "en": "Protein: {p} g",
        "de": "Eiweiß: {p} g",
        "uk": "Білки: {p} г",
    },
    "meal_fat": {
        "en": "Fat: {f} g (sat. {sat} g)",
        "de": "Fett: {f} g (ges. {sat} g)",
        "uk": "Жири: {f} г (у т.ч. насичені {sat} г)",
    },
    "meal_carb": {
        "en": "Carbohydrate: {c} g (sugars {s} g)",
        "de": "Kohlenhydrate: {c} g (davon Zucker {s} g)",
        "uk": "Вуглеводи: {c} г (у т.ч. цукри {s} г)",
    },
    "meal_sodium": {
        "en": "Sodium: {mg} mg",
        "de": "Natrium: {mg} mg",
        "uk": "Натрій: {mg} мг",
    },
    "nutrient_excellent": {
        "en": "Excellent",
        "de": "Ausgezeichnete",
        "uk": "Відмінне",
    },
    "nutrient_good": {
        "en": "Good",
        "de": "Gute",
        "uk": "Добре",
    },
    "nutrient_source_line": {
        "en": "{verb} source of {nutrient} ({pct}% DV)",
        "de": "{verb} Quelle für {nutrient} ({pct}% des Tagesbedarfs)",
        "uk": "{verb} джерело {nutrient} ({pct}% від денної норми)",
    },
    "approve_button": {
        "en": "Approve",
        "de": "Genehmigen",
        "uk": "Схвалити",
    },
    "deny_button": {
        "en": "Deny",
        "de": "Ablehnen",
        "uk": "Відхилити",
    },
    "approval_prompt": {
        "en": "The assistant wants to call a tool:\n\n{call}\n\nApprove this action?",
        "de": "Der Assistent möchte ein Tool aufrufen:\n\n{call}\n\nDiese Aktion genehmigen?",
        "uk": "Асистент хоче викликати інструмент:\n\n{call}\n\nСхвалити цю дію?",
    },
    "auto_call_notice": {
        "en": "Called tool (auto-approved):\n\n{call}",
        "de": "Tool aufgerufen (automatisch genehmigt):\n\n{call}",
        "uk": "Викликано інструмент (автоматично схвалено):\n\n{call}",
    },
    "approval_verdict_approved": {
        "en": "APPROVED",
        "de": "GENEHMIGT",
        "uk": "СХВАЛЕНО",
    },
    "approval_verdict_denied": {
        "en": "DENIED",
        "de": "ABGELEHNT",
        "uk": "ВІДХИЛЕНО",
    },
    "approval_something_wrong": {
        "en": "Something went wrong.",
        "de": "Etwas ist schiefgelaufen.",
        "uk": "Щось пішло не так.",
    },
    "not_authorized": {
        "en": "You are not authorized to use this bot.",
        "de": "Du bist nicht berechtigt, diesen Bot zu nutzen.",
        "uk": "Ти не маєш доступу до цього бота.",
    },
    "not_authorized_alert": {
        "en": "Not authorized.",
        "de": "Nicht berechtigt.",
        "uk": "Немає доступу.",
    },
}

MACRO_LABELS_I18N: dict[str, dict[str, str]] = {
    "energy_kcal_serving": {"en": "Energy", "de": "Energie", "uk": "Енергія"},
    "protein_g_serving": {"en": "Protein", "de": "Eiweiß", "uk": "Білки"},
    "fat_g_serving": {"en": "Fat", "de": "Fett", "uk": "Жири"},
    "saturated_fat_g_serving": {"en": "Saturated Fat", "de": "Gesättigte Fettsäuren", "uk": "Насичені жири"},
    "carbohydrate_g_serving": {"en": "Carbohydrate", "de": "Kohlenhydrate", "uk": "Вуглеводи"},
    "sugars_g_serving": {"en": "Sugars", "de": "Zucker", "uk": "Цукри"},
    "sodium_mg_serving": {"en": "Sodium", "de": "Natrium", "uk": "Натрій"},
}

MACRO_UNITS_I18N: dict[str, dict[str, str]] = {
    "energy_kcal_serving": {"en": "kcal", "de": "kcal", "uk": "ккал"},
    "protein_g_serving": {"en": "g", "de": "g", "uk": "г"},
    "fat_g_serving": {"en": "g", "de": "g", "uk": "г"},
    "saturated_fat_g_serving": {"en": "g", "de": "g", "uk": "г"},
    "carbohydrate_g_serving": {"en": "g", "de": "g", "uk": "г"},
    "sugars_g_serving": {"en": "g", "de": "g", "uk": "г"},
    "sodium_mg_serving": {"en": "mg", "de": "mg", "uk": "мг"},
}

NUTRIENT_LABELS_I18N: dict[str, dict[str, str]] = {
    "vitamin_a_mcg": {"en": "Vitamin A", "de": "Vitamin A", "uk": "Вітамін A"},
    "beta_carotene_mcg": {"en": "Beta-carotene", "de": "Beta-Carotin", "uk": "Бета-каротин"},
    "vitamin_d_mcg": {"en": "Vitamin D", "de": "Vitamin D", "uk": "Вітамін D"},
    "vitamin_e_mg": {"en": "Vitamin E", "de": "Vitamin E", "uk": "Вітамін E"},
    "vitamin_k_mcg": {"en": "Vitamin K", "de": "Vitamin K", "uk": "Вітамін K"},
    "vitamin_b1_mg": {"en": "Thiamin (B1)", "de": "Thiamin (B1)", "uk": "Тіамін (B1)"},
    "vitamin_b2_mg": {"en": "Riboflavin (B2)", "de": "Riboflavin (B2)", "uk": "Рибофлавін (B2)"},
    "niacin_mg": {"en": "Niacin (B3)", "de": "Niacin (B3)", "uk": "Ніацин (B3)"},
    "vitamin_b6_mg": {"en": "Vitamin B6", "de": "Vitamin B6", "uk": "Вітамін B6"},
    "folate_mcg": {"en": "Folate", "de": "Folat", "uk": "Фолієва кислота"},
    "pantothenic_acid_mg": {
        "en": "Pantothenic Acid (B5)",
        "de": "Pantothensäure (B5)",
        "uk": "Пантотенова кислота (B5)",
    },
    "biotin_mcg": {"en": "Biotin (B7)", "de": "Biotin (B7)", "uk": "Біотин (B7)"},
    "vitamin_b12_mcg": {"en": "Vitamin B12", "de": "Vitamin B12", "uk": "Вітамін B12"},
    "vitamin_c_mg": {"en": "Vitamin C", "de": "Vitamin C", "uk": "Вітамін C"},
    "chloride_mg": {"en": "Chloride", "de": "Chlorid", "uk": "Хлорид"},
    "potassium_mg": {"en": "Potassium", "de": "Kalium", "uk": "Калій"},
    "calcium_mg": {"en": "Calcium", "de": "Calcium", "uk": "Кальцій"},
    "phosphorus_mg": {"en": "Phosphorus", "de": "Phosphor", "uk": "Фосфор"},
    "magnesium_mg": {"en": "Magnesium", "de": "Magnesium", "uk": "Магній"},
    "iron_mg": {"en": "Iron", "de": "Eisen", "uk": "Залізо"},
    "iodine_mcg": {"en": "Iodine", "de": "Jod", "uk": "Йод"},
    "fluoride_mg": {"en": "Fluoride", "de": "Fluorid", "uk": "Фторид"},
    "zinc_mg": {"en": "Zinc", "de": "Zink", "uk": "Цинк"},
    "selenium_mcg": {"en": "Selenium", "de": "Selen", "uk": "Селен"},
    "copper_mg": {"en": "Copper", "de": "Kupfer", "uk": "Мідь"},
    "manganese_mg": {"en": "Manganese", "de": "Mangan", "uk": "Марганець"},
    "chromium_mcg": {"en": "Chromium", "de": "Chrom", "uk": "Хром"},
    "molybdenum_mcg": {"en": "Molybdenum", "de": "Molybdän", "uk": "Молібден"},
    "boron_mg": {"en": "Boron", "de": "Bor", "uk": "Бор"},
    "silicon_mg": {"en": "Silicon", "de": "Silizium", "uk": "Кремній"},
}


def t(key: str, lang: str, **kwargs: object) -> str:
    catalog = STRINGS[key]
    template = catalog.get(lang, catalog[DEFAULT_LANGUAGE])
    return template.format(**kwargs) if kwargs else template


def macro_label(field: str, lang: str) -> str:
    labels = MACRO_LABELS_I18N[field]
    return labels.get(lang, labels[DEFAULT_LANGUAGE])


def macro_unit(field: str, lang: str) -> str:
    units = MACRO_UNITS_I18N[field]
    return units.get(lang, units[DEFAULT_LANGUAGE])


def nutrient_label(field: str, lang: str) -> str:
    labels = NUTRIENT_LABELS_I18N[field]
    return labels.get(lang, labels[DEFAULT_LANGUAGE])
