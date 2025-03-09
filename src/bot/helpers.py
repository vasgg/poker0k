import logging
from aiogram import Bot

logging = logging.getLogger(__name__)


async def on_startup(bot: Bot, settings):
    try:
        for chat_id in settings.TG_BOT_ADMIN_ID, settings.TG_REPORTS_CHAT:
            await bot.send_message(
                chat_id,
                "<b>Worker started</b>\n\n/balance for check balance",
                disable_notification=True,
            )
    except:
        logging.warning("Failed to send on shutdown notify")


async def on_shutdown(bot: Bot, settings):
    try:
        for chat_id in settings.TG_BOT_ADMIN_ID, settings.TG_REPORTS_CHAT:
            await bot.send_message(
                chat_id,
                "<b>Worker stopped</b>",
                disable_notification=True,
            )
    except:
        logging.warning("Failed to send on shutdown notify")
