from __future__ import annotations

import os
import signal
import subprocess
import sys

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand


def terminate_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)
        process.wait(timeout=5)
        return
    except Exception:
        pass

    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        process.kill()


class Command(StaticfilesRunserverCommand):
    help = "Starts the Django development server and the Telegram bot."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--skip-telegram-bot",
            action="store_true",
            help="Start the Django server without the Telegram bot process.",
        )
        parser.add_argument(
            "--telegram-drop-pending-updates",
            action="store_true",
            help="Drop pending Telegram updates before bot polling starts.",
        )

    def start_telegram_bot(self, options) -> subprocess.Popen | None:
        if options["skip_telegram_bot"]:
            self.stdout.write("Telegram bot autostart skipped.")
            return None

        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(self.style.WARNING("Telegram bot was not started: TELEGRAM_BOT_TOKEN is not configured."))
            return None

        if options["use_reloader"] and os.environ.get("RUN_MAIN") != "true":
            return None

        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        command = [sys.executable, "manage.py", "run_telegram_bot"]
        if options["telegram_drop_pending_updates"]:
            command.append("--drop-pending-updates")

        self.stdout.write("Starting Telegram bot process...")
        return subprocess.Popen(
            command,
            cwd=str(settings.BASE_DIR),
            creationflags=creationflags,
        )

    def stop_telegram_bot(self, process: subprocess.Popen | None) -> None:
        terminate_process(process)

    def inner_run(self, *args, **options):
        bot_process = self.start_telegram_bot(options)
        try:
            super().inner_run(*args, **options)
        finally:
            self.stop_telegram_bot(bot_process)
