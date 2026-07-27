from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Advantage, HomePageSettings, ProductRow, ServiceCard, SiteSettings


class AdminThemeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser("admin", "admin@example.com", "pass12345")
        self.client.force_login(self.user)

    def test_admin_is_forced_light_and_has_no_theme_toggle(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin_custom/admin.css")
        self.assertNotContains(response, "admin/css/dark_mode.css")
        self.assertNotContains(response, "admin/js/theme.js")
        self.assertNotContains(response, 'class="theme-toggle"')
        self.assertNotContains(response, 'id="core-application"')
        self.assertNotContains(response, 'aria-describedby="core-application"')
        self.assertContains(response, "Выберите своё")
        self.assertNotContains(response, "Материалы и детали")

    def test_product_row_admin_uses_section_name(self):
        response = self.client.get(reverse("admin:core_productrow_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Секцию «Выберите своё»")
        self.assertNotContains(response, "Материал и деталь")

    def test_singleton_admin_redirects_to_change_form(self):
        settings = HomePageSettings.get_solo()

        changelist_response = self.client.get(reverse("admin:core_homepagesettings_changelist"))
        add_response = self.client.get(reverse("admin:core_homepagesettings_add"))

        self.assertRedirects(changelist_response, reverse("admin:core_homepagesettings_change", args=[settings.pk]))
        self.assertRedirects(add_response, reverse("admin:core_homepagesettings_change", args=[settings.pk]))

    def test_site_settings_admin_contains_logo_and_favicon_fields(self):
        settings = SiteSettings.get_solo()

        response = self.client.get(reverse("admin:core_sitesettings_change", args=[settings.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="logo"')
        self.assertContains(response, 'name="favicon"')
        self.assertContains(response, "Превью логотипа")
        self.assertContains(response, "admin_custom/image_preview.js")
        self.assertContains(response, 'data-preview-target="preview-logo"')
        self.assertContains(response, 'id="preview-logo"')

    def test_home_settings_admin_contains_main_images(self):
        settings = HomePageSettings.get_solo()

        response = self.client.get(reverse("admin:core_homepagesettings_change", args=[settings.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="hero_book_image"')
        self.assertContains(response, 'name="hero_calendar_image"')
        self.assertContains(response, 'name="hero_planner_image"')
        self.assertContains(response, 'name="hero_diploma_image"')
        self.assertContains(response, 'name="gift_image"')
        self.assertContains(response, 'data-preview-target="preview-hero_book_image"')
        self.assertContains(response, 'id="preview-hero_book_image"')

    def test_admin_labels_are_shown_in_russian(self):
        site_settings = SiteSettings.get_solo()
        home_settings = HomePageSettings.get_solo()

        site_response = self.client.get(reverse("admin:core_sitesettings_change", args=[site_settings.pk]))
        home_response = self.client.get(reverse("admin:core_homepagesettings_change", args=[home_settings.pk]))

        self.assertContains(site_response, "Электронная почта")
        self.assertContains(site_response, "Ссылка на Telegram")
        self.assertContains(site_response, "Ссылка на MAX")
        self.assertContains(site_response, "Телефон без форматирования")
        self.assertContains(site_response, "Ссылка для звонка")
        self.assertContains(site_response, "Превью иконки сайта")
        self.assertNotContains(site_response, "Email для заявок")
        self.assertNotContains(site_response, "Phone digits")
        self.assertNotContains(site_response, "Phone href")

        self.assertContains(home_response, "Поисковая оптимизация")
        self.assertContains(home_response, "Поисковый заголовок")
        self.assertContains(home_response, "Описание изображения книги")
        self.assertContains(home_response, "Форма и призыв к действию")
        self.assertNotContains(home_response, "SEO title")
        self.assertNotContains(home_response, "Hero eyebrow")

    def test_service_card_admin_contains_image_field(self):
        response = self.client.get(reverse("admin:core_servicecard_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="image"')
        self.assertContains(response, "Превью изображения")
        self.assertContains(response, 'data-preview-target="preview-image"')
        self.assertContains(response, 'id="preview-image"')

    def test_product_row_admin_contains_image_field(self):
        response = self.client.get(reverse("admin:core_productrow_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="image"')
        self.assertContains(response, "Секция «Выберите своё»")

    def test_advantage_admin_contains_image_field(self):
        advantage = Advantage.objects.create(title="Быстро", description="Описание")

        response = self.client.get(reverse("admin:core_advantage_change", args=[advantage.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="image"')
        self.assertContains(response, 'name="image_alt"')
