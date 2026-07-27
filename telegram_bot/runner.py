from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from django.conf import settings

from telegram_bot.bootstrap import setup_django

setup_django()

from telegram_bot.handlers import router  # noqa: E402

logger = logging.getLogger(__name__)


async def run_bot(*, drop_pending_updates: bool = False) -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    logger.info("Starting Telegram bot polling")
    try:
        await bot.delete_webhook(drop_pending_updates=drop_pending_updates)
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()
