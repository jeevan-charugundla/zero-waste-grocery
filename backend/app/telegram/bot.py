"""
Freshwise Telegram Bot Entrypoint & Worker Application.

Runs the Telegram bot with long-polling and manages the background
proactive reminder scheduler.

Usage:
    cd backend
    .venv/Scripts/python.exe -m app.telegram.bot
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Any

from telegram.ext import Application, ApplicationBuilder

from app.config import get_settings
from app.telegram.handlers import register_handlers
from app.telegram.reminders import run_reminder_scheduler

logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("freshwise.telegram.main")


async def global_error_handler(update: object, context: Any) -> None:
    """Log uncaught errors and prevent worker crashing."""
    err = getattr(context, "error", None)
    logger.error("Uncaught exception in Telegram handler: %s", err, exc_info=err)


def create_bot_application() -> Application:
    """
    Instantiate and configure the python-telegram-bot Application.
    Loads the token safely from backend settings.
    """
    settings = get_settings()
    token = settings.telegram_bot_token.strip()

    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not set in backend/.env. "
            "Please configure TELEGRAM_BOT_TOKEN to run the bot."
        )

    # Build the Application
    app = ApplicationBuilder().token(token).build()

    # Register error handler
    app.add_error_handler(global_error_handler)

    # Register command, callback, and message handlers
    register_handlers(app)

    return app



async def run_bot_async() -> None:
    """Async runner that manages both Telegram long-polling and the reminder scheduler."""
    settings = get_settings()
    logger.info("Initializing Freshwise Telegram Bot...")

    try:
        app = create_bot_application()
    except ValueError as exc:
        logger.error("Configuration Error: %s", exc)
        sys.exit(1)

    # Initialize bot
    await app.initialize()
    await app.start()

    # Print masked token log
    bot_info = await app.bot.get_me()
    logger.info(
        "✓ Telegram Bot online: @%s (ID: %d)",
        bot_info.username,
        bot_info.id,
    )
    logger.info(
        "Manager authorization: %d allowlisted Telegram user ID(s) configured.",
        len(settings.allowed_telegram_user_ids),
    )

    # Start long polling
    await app.updater.start_polling(drop_pending_updates=True)

    # Start proactive reminder scheduler background task
    scheduler_task = None
    if settings.telegram_reminders_enabled:
        scheduler_task = asyncio.create_task(run_reminder_scheduler(app.bot))
        logger.info("Proactive reminder scheduler task spawned.")

    # Keep running until cancelled
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig:
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                # Windows does not support add_signal_handler in all event loop implementations
                pass

    try:
        logger.info("Bot is running and listening for messages. Press Ctrl+C to stop.")
        while not stop_event.is_set():
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received.")
    finally:
        logger.info("Stopping bot and scheduler...")
        if scheduler_task and not scheduler_task.done():
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass

        if app.updater.running:
            await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("Freshwise Telegram Bot shutdown cleanly.")


def main() -> None:
    """CLI Entrypoint for running the bot worker."""
    try:
        asyncio.run(run_bot_async())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
