from .clear import CLEAR_COMMAND, build_clear_handler
from .day_summary import DAY_SUMMARY_COMMAND, build_day_summary_handler
from .destroy import DESTROY_COMMAND, build_destroy_handler
from .profile import PROFILE_COMMAND, build_profile_handler
from .start import START_COMMAND, build_start_handler
from .timezone import TIMEZONE_COMMAND, build_timezone_callback_handler, build_timezone_handler
from .week_summary import WEEK_SUMMARY_COMMAND, build_week_summary_handler

# Registered with Telegram (set_my_commands) so the "/" menu stays in sync
# with the handlers below instead of needing manual BotFather setup.
BOT_COMMANDS = [
    START_COMMAND,
    PROFILE_COMMAND,
    TIMEZONE_COMMAND,
    DAY_SUMMARY_COMMAND,
    WEEK_SUMMARY_COMMAND,
    DESTROY_COMMAND,
    CLEAR_COMMAND,
]

__all__ = [
    "BOT_COMMANDS",
    "build_clear_handler",
    "build_day_summary_handler",
    "build_destroy_handler",
    "build_profile_handler",
    "build_start_handler",
    "build_timezone_callback_handler",
    "build_timezone_handler",
    "build_week_summary_handler",
]
