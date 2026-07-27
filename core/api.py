from __future__ import annotations

import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from core.forms import ApplicationForm
from core.models import HomePageSettings, SiteSettings
from core.seed import ensure_default_content
from core.utils import (
    TELEGRAM_SUBSCRIBED_MESSAGE,
    TELEGRAM_UNSUBSCRIBED_MESSAGE,
    notify_application,
    send_telegram_message,
    upsert_telegram_subscriber,
)

logger = logging.getLogger(__name__)


def build_form_error_payload(form: ApplicationForm) -> dict:
    errors = {
        field_name: [item["message"] for item in items]
        for field_name, items in form.errors.get_json_data(escape_html=True).items()
    }
    return {
        "ok": False,
        "success": False,
        "message": "Пожалуйста, проверьте форму.",
        "errors": errors,
        "error_details": form.errors.get_json_data(),
    }


@require_POST
def submit_application(request):
    ensure_default_content()
    form = ApplicationForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse(build_form_error_payload(form), status=HTTP_400_BAD_REQUEST)

    application = form.save(source_url=request.META.get("HTTP_REFERER", ""))
    notify_application(application, site_settings=SiteSettings.get_solo())
    home_settings = HomePageSettings.get_solo()
    return JsonResponse(
        {
            "ok": True,
            "success": True,
            "message": home_settings.success_text,
            "title": home_settings.success_title,
            "application_id": application.pk,
        },
        status=HTTP_201_CREATED,
    )


class TelegramWebhookApiView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, token: str) -> Response:
        if not settings.TELEGRAM_BOT_TOKEN or token != settings.TELEGRAM_BOT_TOKEN:
            return Response(status=HTTP_404_NOT_FOUND)

        message = request.data.get("message") or request.data.get("edited_message") or {}
        chat_data = message.get("chat") or {}
        text = (message.get("text") or "").strip()

        if text.startswith("/start"):
            subscriber = upsert_telegram_subscriber(chat_data, is_active=True)
            if subscriber:
                try:
                    send_telegram_message(TELEGRAM_SUBSCRIBED_MESSAGE, subscriber.chat_id)
                except Exception:
                    logger.exception("Не удалось отправить подтверждение подписки в Telegram %s", subscriber.chat_id)
        elif text.startswith("/stop"):
            subscriber = upsert_telegram_subscriber(chat_data, is_active=False)
            if subscriber:
                try:
                    send_telegram_message(TELEGRAM_UNSUBSCRIBED_MESSAGE, subscriber.chat_id)
                except Exception:
                    logger.exception("Не удалось отправить подтверждение отписки в Telegram %s", subscriber.chat_id)

        return Response({"ok": True})
