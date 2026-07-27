from __future__ import annotations

import json
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.admin import TelegramSubscriberAdmin
from core.models import (
    Advantage,
    Application,
    HomePageSettings,
    ProcessStep,
    ProductRow,
    ServiceCard,
    SiteSettings,
    TelegramSubscriber,
)
from core.utils import notify_application


class ApplicationSubmissionTests(TestCase):
    def setUp(self):
        self.service = ServiceCard.objects.create(title="Тестовая услуга")

    @patch("core.api.notify_application")
    def test_submit_application_api_creates_record(self, notify_application_mock):
        response = self.client.post(
            reverse("submit_application"),
            data={
                "name": "Иван",
                "phone": "+7 (921) 111-22-33",
                "email": "ivan@example.com",
                "service": str(self.service.pk),
                "comment": "Нужна консультация",
                "consent": "1",
                "website": "",
            },
            HTTP_REFERER="http://testserver/",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Application.objects.count(), 1)
        application = Application.objects.get()
        self.assertEqual(application.service, self.service)
        self.assertEqual(application.email, "ivan@example.com")
        self.assertEqual(response.json()["ok"], True)
        self.assertEqual(response.json()["success"], True)
        notify_application_mock.assert_called_once()

    @patch("core.api.notify_application")
    def test_home_post_uses_same_submission_flow(self, notify_application_mock):
        response = self.client.post(
            reverse("home"),
            data={
                "name": "Иван",
                "phone": "+7 (921) 111-22-33",
                "email": "ivan@example.com",
                "service": str(self.service.pk),
                "comment": "Нужен расчет",
                "consent": "1",
                "website": "",
            },
            HTTP_REFERER="http://testserver/",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(response.json()["ok"], True)
        notify_application_mock.assert_called_once()

    def test_submit_application_returns_flat_json_errors(self):
        response = self.client.post(
            reverse("submit_application"),
            data={
                "name": "И",
                "phone": "123",
                "email": "not-an-email",
                "service": "",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["success"], False)
        self.assertIsInstance(payload["errors"]["email"][0], str)
        self.assertIsInstance(payload["errors"]["phone"][0], str)
        self.assertIn("service", payload["errors"])

    def test_submit_application_returns_json_error_for_oversized_file(self):
        oversized_file = SimpleUploadedFile(
            "brief.pdf",
            b"x" * (3 * 1024 * 1024),
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("submit_application"),
            data={
                "name": "Иван",
                "phone": "+7 (921) 111-22-33",
                "email": "ivan@example.com",
                "service": str(self.service.pk),
                "comment": "Нужен расчет",
                "consent": "1",
                "website": "",
                "file": oversized_file,
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["ok"], False)
        self.assertIn("file", payload["errors"])


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    APPLICATION_NOTIFICATION_EMAIL="notify@example.com",
    TELEGRAM_BOT_TOKEN="",
    TELEGRAM_CHAT_ID="",
)
class EmailNotificationTests(TestCase):
    def test_notify_application_sends_html_email(self):
        site_settings = SiteSettings.get_solo()
        site_settings.application_email = "notify@example.com"
        site_settings.save(update_fields=["application_email"])
        service = ServiceCard.objects.create(title="Тестовая услуга")
        application = Application.objects.create(
            name="Иван",
            phone="+7 (921) 111-22-33",
            email="ivan@example.com",
            service=service,
            comment="Позвоните сегодня",
            consent=True,
        )

        result = notify_application(application, site_settings)

        self.assertTrue(result["email"])
        self.assertFalse(result["telegram"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Новая заявка с сайта")
        self.assertIn("Иван", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        html_body, mimetype = mail.outbox[0].alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn("Новая заявка с сайта", html_body)
        self.assertIn("Тестовая услуга", html_body)


class TelegramNotificationTests(TestCase):
    @override_settings(TELEGRAM_BOT_TOKEN="test-bot-token")
    @patch("core.utils.requests.post")
    def test_notify_application_sends_to_all_active_telegram_subscribers(self, requests_post_mock):
        TelegramSubscriber.objects.create(chat_id="111", username="first", is_active=True)
        TelegramSubscriber.objects.create(chat_id="222", username="second", is_active=True)
        TelegramSubscriber.objects.create(chat_id="333", username="inactive", is_active=False)
        service = ServiceCard.objects.create(title="Тестовая услуга")
        application = Application.objects.create(
            name="Иван",
            phone="+7 (921) 111-22-33",
            email="ivan@example.com",
            service=service,
            consent=True,
        )

        result = notify_application(application, SiteSettings.objects.first())

        self.assertTrue(result["telegram"])
        self.assertEqual(requests_post_mock.call_count, 2)
        chat_ids = sorted(call.kwargs["data"]["chat_id"] for call in requests_post_mock.call_args_list)
        self.assertEqual(chat_ids, ["111", "222"])


@override_settings(TELEGRAM_BOT_TOKEN="test-bot-token", TELEGRAM_CHAT_ID="")
class TelegramWebhookTests(TestCase):
    @patch("core.api.send_telegram_message")
    def test_start_subscribes_chat(self, send_telegram_message_mock):
        response = self.client.post(
            reverse("telegram_webhook_api", kwargs={"token": "test-bot-token"}),
            data=json.dumps(
                {
                    "update_id": 1,
                    "message": {
                        "message_id": 10,
                        "text": "/start",
                        "chat": {
                            "id": 123456,
                            "username": "cleaning_admin",
                            "first_name": "Иван",
                            "last_name": "Петров",
                        },
                    },
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(TelegramSubscriber.objects.count(), 1)
        subscriber = TelegramSubscriber.objects.get()
        self.assertEqual(subscriber.chat_id, "123456")
        self.assertTrue(subscriber.is_active)
        self.assertEqual(subscriber.username, "cleaning_admin")
        send_telegram_message_mock.assert_called_once_with(
            "Вы подписались на уведомления о новых заявках.",
            "123456",
        )

    @patch("core.api.send_telegram_message")
    def test_stop_deactivates_chat(self, send_telegram_message_mock):
        TelegramSubscriber.objects.create(chat_id="123456", username="cleaning_admin", is_active=True)

        response = self.client.post(
            reverse("telegram_webhook_api", kwargs={"token": "test-bot-token"}),
            data=json.dumps(
                {
                    "update_id": 2,
                    "message": {
                        "message_id": 11,
                        "text": "/stop",
                        "chat": {
                            "id": 123456,
                            "username": "cleaning_admin",
                            "first_name": "Иван",
                        },
                    },
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TelegramSubscriber.objects.get(chat_id="123456").is_active)
        send_telegram_message_mock.assert_called_once_with(
            "Вы отписались от уведомлений о новых заявках.",
            "123456",
        )


class TelegramBotCommandTests(TestCase):
    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_run_telegram_bot_requires_token(self):
        with self.assertRaisesMessage(CommandError, "TELEGRAM_BOT_TOKEN is not configured."):
            call_command("run_telegram_bot")

    @override_settings(TELEGRAM_BOT_TOKEN="test-bot-token")
    @patch("core.management.commands.run_telegram_bot.asyncio.run")
    @patch("core.management.commands.run_telegram_bot.run_bot", new_callable=Mock)
    def test_run_telegram_bot_starts_aiogram_runner(self, run_bot_mock, asyncio_run_mock):
        run_bot_mock.return_value = object()

        call_command("run_telegram_bot", "--drop-pending-updates")

        run_bot_mock.assert_called_once_with(drop_pending_updates=True)
        asyncio_run_mock.assert_called_once_with(run_bot_mock.return_value)


class TelegramSubscriberAdminTests(SimpleTestCase):
    def test_subscriber_admin_disables_add(self):
        admin_instance = TelegramSubscriberAdmin(TelegramSubscriber, AdminSite())
        self.assertFalse(admin_instance.has_add_permission(None))


class SiteContentSyncCommandTests(TestCase):
    def setUp(self):
        self.temp_media = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.media_override.enable()

        SiteSettings.get_solo()
        HomePageSettings.get_solo()
        ServiceCard.objects.create(order=1, title="Старое название")
        ProductRow.objects.create(order=2, title="Старый продукт", reverse=False)

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()
        super().tearDown()

    def test_seed_site_content_sync_populates_existing_records_and_images(self):
        call_command("seed_site_content", "--sync")

        site = SiteSettings.get_solo()
        self.assertEqual(site.site_name, "Точка дизайна и печати")
        self.assertTrue(site.logo.name)
        self.assertTrue(site.favicon.name)

        home = HomePageSettings.get_solo()
        self.assertEqual(home.seo_title, "Точка дизайна и печати — идеи, которые можно держать в руках")
        self.assertEqual(home.hero_eyebrow, "Дизайн-студия и печать")
        self.assertEqual(home.gift_eyebrow, "Фотоподарки")
        self.assertTrue(home.hero_book_image.name)
        self.assertTrue(home.gift_image.name)

        self.assertEqual(ServiceCard.objects.count(), 6)
        self.assertEqual(ProductRow.objects.count(), 4)
        self.assertEqual(Advantage.objects.count(), 4)
        self.assertEqual(ProcessStep.objects.count(), 4)

        service = ServiceCard.objects.get(order=1)
        self.assertEqual(service.title, "Дипломы, грамоты и сертификаты")
        self.assertEqual(service.form_label, "Дипломы, грамоты и сертификаты")
        self.assertTrue(service.image.name.endswith(".webp"))

        product = ProductRow.objects.get(order=2)
        self.assertEqual(product.title, "Фотокалендари")
        self.assertTrue(product.reverse)
        self.assertEqual(product.service_label, "Фотокалендари")
        self.assertTrue(product.image.name.endswith(".webp"))
