import logging

from .agent import build_agent
from .commands import BOT_COMMANDS
from .config import load_settings
from .conversation import ConversationService
from .db import Database
from .meals import MealService
from .nutrition import build_nutrition_agent
from .telegram_bot import TelegramBot


def main() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level.upper(), format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    db = Database(settings.database_path)
    agent = build_agent(settings)
    nutrition_agent = build_nutrition_agent(settings)
    conversations = ConversationService(db, agent)
    meals = MealService(db, nutrition_agent)
    bot = TelegramBot(settings, conversations, meals)

    # MCPToolset (streamable HTTP) opens/closes its own connection per run,
    # so the only resource we need to bind to the app lifecycle is the DB.
    async def _post_init(_):
        await db.connect()
        await bot.application.bot.set_my_commands(BOT_COMMANDS)

    async def _post_shutdown(_):
        await db.close()

    bot.application.post_init = _post_init
    bot.application.post_shutdown = _post_shutdown

    try:
        bot.run()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Interrupted during shutdown, exiting.")


if __name__ == "__main__":
    main()
