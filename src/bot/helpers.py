import logging

from aiogram import Bot

from controllers.telegram import send_telegram_report

logger = logging.getLogger(__name__)


async def _notify(
    bot: Bot,
    settings,
    message: str,
) -> None:
    chats = (settings.TG_BOT_ADMIN_ID, settings.TG_REPORTS_CHAT)
    try:
        for chat_id in chats:
            await bot.send_message(chat_id, message, disable_notification=True)
    except Exception as exc:
        logger.warning("Failed to deliver message via bot API, falling back to HTTP sender: %s", exc, exc_info=True)
        try:
            await send_telegram_report(
                message=message,
                chats=chats,
                disable_notification=True,
            )
        except Exception:
            logger.exception("Fallback Telegram notification failed")


async def on_startup(bot: Bot, settings):
    await _notify(
        bot,
        settings,
        "<b>Worker started</b>\n\nuse <code>/balance</code> for check balance",
    )


async def on_shutdown(bot: Bot, settings):
    await _notify(
        bot,
        settings,
        "<b>Worker stopped</b>",
    )
