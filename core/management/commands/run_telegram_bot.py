from __future__ import annotations

import asyncio

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from telegram_bot.runner import run_bot


class Command(BaseCommand):
    help = "Runs the Telegram bot via aiogram long polling."

    def add_arguments(self, parser):
        parser.add_argument(
            "--drop-pending-updates",
            action="store_true",
            help="Drop pending Telegram updates before polling starts.",
        )

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN is not configured.")

        asyncio.run(run_bot(drop_pending_updates=options["drop_pending_updates"]))
