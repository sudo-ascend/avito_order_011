from __future__ import annotations

from django import forms
from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

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

admin.site.site_header = "Точка дизайна и печати"
admin.site.site_title = "Точка дизайна и печати"
admin.site.index_title = "Управление сайтом"


def render_admin_file_preview(field_file, preview_id: str):
    image_url = field_file.url if field_file else ""
    wrapper_class = "admin-image-preview" if image_url else "admin-image-preview is-empty"
    link_class = "admin-image-preview-link" if image_url else "admin-image-preview-link is-hidden"
    image_class = "admin-image-preview-image" if image_url else "admin-image-preview-image is-hidden"
    placeholder_class = "admin-image-preview-placeholder is-hidden" if image_url else "admin-image-preview-placeholder"
    return format_html(
        '<div class="{}" id="{}" data-original-url="{}">'
        '<a class="{}" href="{}" target="_blank" rel="noopener noreferrer">'
        '<img class="{}" src="{}" alt=""></a>'
        '<span class="{}">Предпросмотр появится здесь</span>'
        "</div>",
        wrapper_class,
        preview_id,
        image_url,
        link_class,
        image_url,
        image_class,
        image_url,
        placeholder_class,
    )


def build_preview_method(field_name: str, description: str):
    @admin.display(description=description)
    def _preview(self, obj):
        return render_admin_file_preview(getattr(obj, field_name, None), f"preview-{field_name}")

    return _preview


class BaseContentAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 4})},
    }
    save_as = False
    save_on_top = True

    class Media:
        js = ("admin_custom/image_preview.js",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield and isinstance(db_field, (models.ImageField, models.FileField)):
            existing_class = formfield.widget.attrs.get("class", "")
            formfield.widget.attrs["class"] = f"{existing_class} admin-image-input".strip()
            formfield.widget.attrs["data-preview-target"] = f"preview-{db_field.name}"
        return formfield


class SingletonAdmin(BaseContentAdmin):
    def _get_singleton(self):
        return self.model.objects.order_by("pk").first()

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("pk")

    def changelist_view(self, request, extra_context=None):
        obj = self._get_singleton()
        if obj:
            return HttpResponseRedirect(
                reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_change", args=[obj.pk])
            )
        return HttpResponseRedirect(reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_add"))

    def add_view(self, request, form_url="", extra_context=None):
        obj = self._get_singleton()
        if obj:
            return HttpResponseRedirect(
                reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_change", args=[obj.pk])
            )
        return super().add_view(request, form_url, extra_context)


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    list_display = ("site_name", "phone", "email", "updated_at")
    readonly_fields = ("phone_digits_display", "phone_href_display", "logo_preview", "favicon_preview", "updated_at")
    fieldsets = (
        ("Основное", {"fields": ("site_name", ("logo", "logo_preview"), ("favicon", "favicon_preview"))}),
        (
            "Контакты",
            {
                "fields": (
                    "phone",
                    "phone_digits_display",
                    "phone_href_display",
                    "email",
                    "application_email",
                    "telegram_url",
                    "max_url",
                    "address",
                    "work_time",
                )
            },
        ),
        ("Подвал", {"fields": ("footer_brand_text", "footer_note", "policy_text")}),
        ("Служебное", {"fields": ("updated_at",)}),
    )

    @admin.display(description="Телефон без форматирования")
    def phone_digits_display(self, obj):
        return obj.phone_digits

    @admin.display(description="Ссылка для звонка")
    def phone_href_display(self, obj):
        return obj.phone_href

    logo_preview = build_preview_method("logo", "Превью логотипа")
    favicon_preview = build_preview_method("favicon", "Превью иконки сайта")


@admin.register(HomePageSettings)
class HomePageSettingsAdmin(SingletonAdmin):
    list_display = ("seo_title", "updated_at")
    readonly_fields = (
        "hero_book_preview",
        "hero_calendar_preview",
        "hero_planner_preview",
        "hero_diploma_preview",
        "gift_preview",
        "updated_at",
    )
    fieldsets = (
        ("Поисковая оптимизация", {"fields": ("seo_title", "seo_description")}),
        (
            "Первый экран",
            {
                "fields": (
                    "hero_eyebrow",
                    "hero_title_part1",
                    "hero_title_part2",
                    "hero_title_emphasis",
                    "hero_lead",
                    "hero_button_label",
                    "hero_channel_label",
                    "hero_secondary_label",
                    "hero_footnote",
                    ("hero_book_image", "hero_book_preview"),
                    "hero_book_alt",
                    ("hero_calendar_image", "hero_calendar_preview"),
                    "hero_calendar_alt",
                    ("hero_planner_image", "hero_planner_preview"),
                    "hero_planner_alt",
                    ("hero_diploma_image", "hero_diploma_preview"),
                    "hero_diploma_alt",
                )
            },
        ),
        (
            "Услуги",
            {"fields": ("services_eyebrow", "services_title_part1", "services_title_part2", "services_title_emphasis", "services_intro")},
        ),
        (
            "Подарить момент",
            {"fields": ("gift_eyebrow", "gift_title_part1", "gift_title_emphasis", "gift_text", "gift_button_label", ("gift_image", "gift_preview"), "gift_image_alt")},
        ),
        (
            "Выберите своё",
            {"fields": ("products_eyebrow", "products_title_part1", "products_title_emphasis", "products_intro")},
        ),
        ("Преимущества", {"fields": ("advantages_eyebrow", "advantages_title_part1", "advantages_title_emphasis")}),
        ("Как заказать", {"fields": ("steps_eyebrow", "steps_title_part1", "steps_title_emphasis", "steps_text")}),
        (
            "Форма и призыв к действию",
            {"fields": ("cta_eyebrow", "cta_title_part1", "cta_title_emphasis", "cta_text", "cta_button_label", "form_title", "form_text", "form_submit_label", "success_title", "success_text")},
        ),
        ("Служебное", {"fields": ("updated_at",)}),
    )

    hero_book_preview = build_preview_method("hero_book_image", "Превью книги")
    hero_calendar_preview = build_preview_method("hero_calendar_image", "Превью календаря")
    hero_planner_preview = build_preview_method("hero_planner_image", "Превью планера")
    hero_diploma_preview = build_preview_method("hero_diploma_image", "Превью диплома")
    gift_preview = build_preview_method("gift_image", "Превью подарка")


@admin.register(ServiceCard)
class ServiceCardAdmin(BaseContentAdmin):
    list_display = ("title", "order", "layout", "button_label", "image_preview")
    list_editable = ("order",)
    list_filter = ("layout",)
    search_fields = ("title", "description", "form_label", "image_alt")
    ordering = ("order", "pk")
    readonly_fields = ("image_preview",)
    fieldsets = (
        ("Услуга", {"fields": ("title", "order", "layout")}),
        ("Текст", {"fields": ("description", "button_label", "form_label")}),
        ("Изображение", {"fields": (("image", "image_preview"), "image_alt")}),
    )

    image_preview = build_preview_method("image", "Превью изображения")


@admin.register(ProductRow)
class ProductRowAdmin(BaseContentAdmin):
    list_display = ("title", "order", "reverse", "image_preview")
    list_editable = ("order", "reverse")
    search_fields = ("title", "lead", "facts_text", "note", "service_label", "image_alt")
    ordering = ("order", "pk")
    readonly_fields = ("image_preview",)
    fieldsets = (
        ("Секция «Выберите своё»", {"fields": ("title", "order", "reverse")}),
        ("Текст", {"fields": ("lead", "facts_text", "note", "button_label", "service_label")}),
        ("Изображение", {"fields": (("image", "image_preview"), "image_alt")}),
    )

    image_preview = build_preview_method("image", "Превью изображения")


@admin.register(Advantage)
class AdvantageAdmin(BaseContentAdmin):
    list_display = ("title", "order", "icon", "image_preview")
    list_editable = ("order",)
    list_filter = ("icon",)
    search_fields = ("title", "description", "image_alt")
    ordering = ("order", "pk")
    readonly_fields = ("image_preview",)
    fieldsets = (
        ("Преимущество", {"fields": ("title", "order")}),
        ("Текст", {"fields": ("description",)}),
        ("Иконка и изображение", {"fields": ("icon", ("image", "image_preview"), "image_alt")}),
    )

    image_preview = build_preview_method("image", "Превью изображения")


@admin.register(ProcessStep)
class ProcessStepAdmin(BaseContentAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)
    search_fields = ("title", "description")
    ordering = ("order", "pk")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "phone", "email", "display_service_admin", "status", "source_url")
    list_filter = ("status", "created_at", "service")
    search_fields = ("name", "phone", "email", "service_name", "comment")
    ordering = ("-created_at", "-pk")
    autocomplete_fields = ("service",)
    readonly_fields = ("created_at", "updated_at", "website", "consent", "source_url", "display_service_admin")
    fieldsets = (
        ("Заявка", {"fields": ("name", "phone", "email", "service", "service_name", "comment", "file")}),
        ("Статус", {"fields": ("status",)}),
        ("Служебное", {"fields": ("consent", "website", "source_url", "display_service_admin", "created_at", "updated_at")}),
    )

    @admin.display(description="Услуга")
    def display_service_admin(self, obj):
        return obj.display_service


@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "username", "first_name", "last_name", "is_active", "subscribed_at", "updated_at")
    list_filter = ("is_active", "subscribed_at", "updated_at")
    search_fields = ("chat_id", "username", "first_name", "last_name")
    readonly_fields = ("chat_id", "username", "first_name", "last_name", "subscribed_at", "updated_at")

    def has_add_permission(self, request):
        return False
