from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Chat, Message
from asgiref.sync import sync_to_async

from core.utils import TELEGRAM_SUBSCRIBED_MESSAGE, TELEGRAM_UNSUBSCRIBED_MESSAGE, upsert_telegram_subscriber

logger = logging.getLogger(__name__)
router = Router()

HELP_MESSAGE = (
    "Команды бота:\n"
    "/start - подписаться на уведомления о новых заявках\n"
    "/stop - отключить уведомления"
)


def build_chat_data(chat: Chat) -> dict[str, int | str | None]:
    return {
        "id": chat.id,
        "username": chat.username,
        "first_name": getattr(chat, "first_name", None),
        "last_name": getattr(chat, "last_name", None),
    }


async def set_subscription(message: Message, *, is_active: bool, reply_text: str) -> None:
    subscriber = await sync_to_async(upsert_telegram_subscriber)(
        build_chat_data(message.chat),
        is_active=is_active,
    )
    if not subscriber:
        logger.warning("Telegram chat %s could not be saved as subscriber", message.chat.id)
        await message.answer("Не удалось определить чат для подписки. Попробуйте еще раз.")
        return

    await message.answer(reply_text)


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await set_subscription(
        message,
        is_active=True,
        reply_text=TELEGRAM_SUBSCRIBED_MESSAGE,
    )


@router.message(Command("stop"))
async def stop_command(message: Message) -> None:
    await set_subscription(
        message,
        is_active=False,
        reply_text=TELEGRAM_UNSUBSCRIBED_MESSAGE,
    )


@router.message()
async def fallback_message(message: Message) -> None:
    await message.answer(HELP_MESSAGE)
