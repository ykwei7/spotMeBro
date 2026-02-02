from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters

from config import TELEGRAM_BOT_TOKEN, validate_config
from handlers import (
    start,
    help_command,
    setgoal_command,
    setunit_command,
    track_start,
    track_input,
    track_fill_exercise,
    track_fill_sets,
    track_fill_reps,
    track_fill_weight,
    track_confirm_button,
    recommend,
    recommend_followup,
    view,
    cancel,
    WAITING_INPUT,
    FILLING_EXERCISE,
    FILLING_SETS,
    FILLING_REPS,
    FILLING_WEIGHT,
    CONFIRMING,
)


async def post_init(application: Application) -> None:
    """Register bot commands so they appear when user taps /."""
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show commands"),
        BotCommand("setgoal", "Set fitness goal"),
        BotCommand("setunit", "Set weight unit (lbs or kg)"),
        BotCommand("track", "Log a lift"),
        BotCommand("recommend", "Get workout suggestion"),
        BotCommand("view", "View past lifts"),
        BotCommand("cancel", "Cancel current action"),
    ])


def main() -> None:
    validate_config()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    track_conv = ConversationHandler(
        entry_points=[CommandHandler("track", track_start)],
        states={
            WAITING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_input)],
            FILLING_EXERCISE: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_fill_exercise)],
            FILLING_SETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_fill_sets)],
            FILLING_REPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_fill_reps)],
            FILLING_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_fill_weight)],
            CONFIRMING: [CallbackQueryHandler(track_confirm_button)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("help", help_command),
            CommandHandler("recommend", recommend),
            CommandHandler("view", view),
            CommandHandler("setgoal", setgoal_command),
            CommandHandler("setunit", setunit_command),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setgoal", setgoal_command))
    app.add_handler(CommandHandler("setunit", setunit_command))
    app.add_handler(track_conv)
    app.add_handler(CommandHandler("recommend", recommend))
    app.add_handler(CommandHandler("view", view))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recommend_followup))

    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
