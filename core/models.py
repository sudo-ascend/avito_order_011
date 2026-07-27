from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from PIL import Image


def parse_text_items(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip(" -•\t") for item in value.replace(",", "\n").splitlines() if item.strip()]


def parse_fact_items(value: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for raw_line in (value or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "|" in line:
            label, text = line.split("|", 1)
        elif ":" in line:
            label, text = line.split(":", 1)
        else:
            label, text = "Пункт", line
        items.append({"label": label.strip(), "value": text.strip()})
    return items


def convert_field_to_webp(field_file: models.fields.files.FieldFile) -> None:
    if not field_file or not field_file.name:
        return
    if field_file.name.lower().endswith(".webp"):
        return

    field_file.open("rb")
    with Image.open(field_file) as image:
        converted = image.convert("RGBA" if image.mode in {"RGBA", "LA", "P"} else "RGB")
        output = BytesIO()
        converted.save(output, format="WEBP", quality=88, optimize=True)

    output.seek(0)
    field_file.save(Path(field_file.name).with_suffix(".webp").as_posix(), ContentFile(output.read()), save=False)


def home_image_upload_to(instance: "HomePageSettings", filename: str) -> str:
    return f"home/{Path(filename).name}"


def service_image_upload_to(instance: "ServiceCard", filename: str) -> str:
    return f"services/{Path(filename).name}"


def product_image_upload_to(instance: "ProductRow", filename: str) -> str:
    return f"products/{Path(filename).name}"


def advantage_image_upload_to(instance: "Advantage", filename: str) -> str:
    return f"advantages/{Path(filename).name}"


def application_file_upload_to(instance: "Application", filename: str) -> str:
    if instance.created_at:
        return f"applications/{instance.created_at:%Y/%m}/{Path(filename).name}"
    return f"applications/pending/{Path(filename).name}"


class WebPImageMixin(models.Model):
    image_fields: tuple[str, ...] = ()

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        for field_name in self.image_fields:
            convert_field_to_webp(getattr(self, field_name))
        super().save(*args, **kwargs)


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj:
            return obj
        return cls.objects.create()


class SiteSettings(SingletonModel):
    site_name = models.CharField("Название сайта", max_length=255, default="Точка дизайна и печати")
    phone = models.CharField("Телефон", max_length=32, blank=True, default="+7 977 807-11-55")
    email = models.EmailField("Электронная почта", blank=True, default="info@tdp.ru")
    telegram_url = models.CharField("Ссылка на Telegram", max_length=255, blank=True, default="tg://resolve?phone=79778071155")
    max_url = models.CharField("Ссылка на MAX", max_length=255, blank=True, default="https://max.ru/channel_TDP")
    application_email = models.EmailField("Электронная почта для заявок", blank=True, default="info@tdp.ru")
    address = models.TextField("Адрес", blank=True)
    work_time = models.CharField("Режим работы", max_length=255, blank=True)
    footer_brand_text = models.TextField(
        "Текст в футере",
        blank=True,
        default="Дизайн, который приятно видеть.\nПечать, которую хочется держать.",
    )
    footer_note = models.CharField("Нижняя строка", max_length=255, blank=True, default="Сделано с вниманием к деталям")
    policy_text = models.TextField(
        "Политика конфиденциальности",
        blank=True,
        default=(
            "Мы используем данные из формы только для обработки вашего обращения и связи по заказу.\n\n"
            "Заявки передаются в защищённую базу данных и используются только для обратной связи.\n\n"
            "Чтобы запросить удаление обращения, напишите на info@tdp.ru."
        ),
    )
    logo = models.ImageField("Логотип", upload_to="site/", blank=True, null=True)
    favicon = models.FileField(
        "Иконка сайта (favicon)",
        upload_to="site/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["ico", "png", "svg"])],
    )
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    image_fields = ("logo",)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self) -> str:
        return self.site_name

    @property
    def phone_digits(self) -> str:
        return "".join(char for char in self.phone if char.isdigit())

    @property
    def phone_href(self) -> str:
        return f"tel:+{self.phone_digits}" if self.phone_digits else "tel:"


class HomePageSettings(SingletonModel):
    seo_title = models.CharField("Поисковый заголовок", max_length=255, blank=True)
    seo_description = models.TextField("Поисковое описание", blank=True)

    hero_eyebrow = models.CharField("Подзаголовок первого экрана", max_length=255, default="Дизайн и печать")
    hero_title_part1 = models.CharField("Заголовок первого экрана, часть 1", max_length=255, default="Идеи, которые")
    hero_title_part2 = models.CharField("Заголовок первого экрана, часть 2", max_length=255, default="можно держать")
    hero_title_emphasis = models.CharField("Акцент в заголовке первого экрана", max_length=255, default="в руках")
    hero_lead = models.TextField(
        "Описание первого экрана",
        default="Дизайн, печать и персональные подарки — с вниманием к каждой детали.",
    )
    hero_button_label = models.CharField("Текст кнопки первого экрана", max_length=120, default="Оставить заявку")
    hero_channel_label = models.CharField("Текст ссылки на канал", max_length=120, default="Канал в MAX")
    hero_secondary_label = models.CharField("Текст дополнительной ссылки первого экрана", max_length=120, default="Смотреть услуги")
    hero_footnote = models.CharField("Подпись первого экрана", max_length=255, default="Маленькая деталь — большое впечатление")

    hero_book_image = models.ImageField("Изображение книги", upload_to=home_image_upload_to, blank=True, null=True)
    hero_book_alt = models.CharField("Описание изображения книги", max_length=255, blank=True)
    hero_calendar_image = models.ImageField("Изображение календаря", upload_to=home_image_upload_to, blank=True, null=True)
    hero_calendar_alt = models.CharField("Описание изображения календаря", max_length=255, blank=True)
    hero_planner_image = models.ImageField("Изображение планера", upload_to=home_image_upload_to, blank=True, null=True)
    hero_planner_alt = models.CharField("Описание изображения планера", max_length=255, blank=True)
    hero_diploma_image = models.ImageField("Изображение диплома", upload_to=home_image_upload_to, blank=True, null=True)
    hero_diploma_alt = models.CharField("Описание изображения диплома", max_length=255, blank=True)

    services_eyebrow = models.CharField("Подзаголовок секции услуг", max_length=255, default="Выберите своё")
    services_title_part1 = models.CharField("Заголовок секции услуг, часть 1", max_length=255, default="Услуги, в которых")
    services_title_part2 = models.CharField("Заголовок секции услуг, часть 2", max_length=255, default="видна")
    services_title_emphasis = models.CharField("Акцент заголовка секции услуг", max_length=255, default="забота")
    services_intro = models.TextField(
        "Описание секции услуг",
        default="Собираем дизайн и печать в целый, живой результат — от первого эскиза до готового изделия.",
    )

    gift_eyebrow = models.CharField("Подзаголовок секции подарка", max_length=255, default="Подарить момент")
    gift_title_part1 = models.CharField("Заголовок секции подарка, часть 1", max_length=255, default="Подарить")
    gift_title_emphasis = models.CharField("Акцент заголовка секции подарка", max_length=255, default="момент")
    gift_text = models.TextField(
        "Текст секции подарка",
        default="Соберём персональный подарок под событие, настроение и человека.",
    )
    gift_button_label = models.CharField("Текст кнопки секции подарка", max_length=120, default="Создать подарок")
    gift_image = models.ImageField("Изображение подарка", upload_to=home_image_upload_to, blank=True, null=True)
    gift_image_alt = models.CharField("Описание изображения подарка", max_length=255, blank=True)

    products_eyebrow = models.CharField("Подзаголовок секции материалов", max_length=255, default="Материалы и детали")
    products_title_part1 = models.CharField("Заголовок секции материалов, часть 1", max_length=255, default="То, что хочется")
    products_title_emphasis = models.CharField("Акцент заголовка секции материалов", max_length=255, default="рассматривать")
    products_intro = models.TextField(
        "Описание секции материалов",
        default=(
            "Здесь — не краткий перечень услуг, а детали каждого изделия: материалы, форматы и возможности "
            "персонализации. Так выбрать своё проще."
        ),
    )

    advantages_eyebrow = models.CharField("Подзаголовок секции преимуществ", max_length=255, default="Подход")
    advantages_title_part1 = models.CharField("Заголовок секции преимуществ, часть 1", max_length=255, default="Почему выбирают")
    advantages_title_emphasis = models.CharField("Акцент заголовка секции преимуществ", max_length=255, default="нас")

    steps_eyebrow = models.CharField("Подзаголовок секции шагов", max_length=255, default="Просто и прозрачно")
    steps_title_part1 = models.CharField("Заголовок секции шагов, часть 1", max_length=255, default="Как")
    steps_title_emphasis = models.CharField("Акцент заголовка секции шагов", max_length=255, default="заказать")
    steps_text = models.TextField(
        "Описание секции шагов",
        default="От первой идеи до момента, когда результат уже у вас в руках.",
    )

    cta_eyebrow = models.CharField("Подзаголовок призыва к действию", max_length=255, default="Давайте начнём")
    cta_title_part1 = models.CharField("Заголовок призыва к действию, часть 1", max_length=255, default="Расскажите о своей идее —")
    cta_title_emphasis = models.CharField(
        "Акцент заголовка призыва к действию",
        max_length=255,
        default="превратим её в красивый результат",
    )
    cta_text = models.TextField("Текст призыва к действию", default="Оставьте заявку, и мы поможем подобрать формат, материалы и стиль.")
    cta_button_label = models.CharField("Текст кнопки призыва к действию", max_length=120, default="Оставить заявку")

    form_title = models.CharField("Заголовок формы", max_length=255, default="Оставить заявку")
    form_text = models.TextField(
        "Текст формы",
        default="Расскажите о задаче — ответим и поможем определиться с форматом.",
    )
    form_submit_label = models.CharField("Текст кнопки отправки формы", max_length=120, default="Отправить заявку")
    success_title = models.CharField("Заголовок сообщения об успехе", max_length=255, default="Спасибо!")
    success_text = models.TextField("Текст сообщения об успехе", default="Заявка отправлена. Мы скоро свяжемся с вами.")

    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    image_fields = ("hero_book_image", "hero_calendar_image", "hero_planner_image", "hero_diploma_image", "gift_image")

    class Meta:
        verbose_name = "Настройки главной"
        verbose_name_plural = "Настройки главной"

    def __str__(self) -> str:
        return "Настройки главной"


class ServiceCard(WebPImageMixin):
    LAYOUT_DEFAULT = "default"
    LAYOUT_WIDE = "wide"
    LAYOUT_DESIGN = "design"
    LAYOUT_PHOTO_BOOKS = "photo_books"

    LAYOUT_CHOICES = (
        (LAYOUT_DEFAULT, "Обычная"),
        (LAYOUT_WIDE, "Широкая"),
        (LAYOUT_DESIGN, "Большая"),
        (LAYOUT_PHOTO_BOOKS, "Фотокниги"),
    )

    order = models.PositiveIntegerField("Порядок", default=10)
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Изображение", upload_to=service_image_upload_to, blank=True, null=True)
    image_alt = models.CharField("Описание изображения", max_length=255, blank=True)
    layout = models.CharField("Вариант карточки", max_length=32, choices=LAYOUT_CHOICES, default=LAYOUT_DEFAULT)
    button_label = models.CharField("Текст кнопки", max_length=120, default="Узнать подробнее")
    form_label = models.CharField("Текст в форме", max_length=255, blank=True)

    image_fields = ("image",)

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.title

    @property
    def extra_classes(self) -> str:
        if self.layout == self.LAYOUT_DEFAULT:
            return ""
        return f"service-card-{self.layout.replace('_', '-')}"

    @property
    def form_title(self) -> str:
        return self.form_label or self.title


class ProductRow(WebPImageMixin):
    order = models.PositiveIntegerField("Порядок", default=10)
    title = models.CharField("Название", max_length=255)
    lead = models.TextField("Краткое описание", blank=True)
    facts_text = models.TextField("Факты", blank=True)
    note = models.TextField("Примечание", blank=True)
    image = models.ImageField("Изображение", upload_to=product_image_upload_to, blank=True, null=True)
    image_alt = models.CharField("Описание изображения", max_length=255, blank=True)
    reverse = models.BooleanField("Сделать в обратную сторону", default=False)
    button_label = models.CharField("Текст кнопки", max_length=120, default="Обсудить заказ")
    service_label = models.CharField("Текст в форме", max_length=255, blank=True)

    image_fields = ("image",)

    class Meta:
        verbose_name = "Секцию «Выберите своё»"
        verbose_name_plural = "Выберите своё"
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.title

    @property
    def facts_list(self) -> list[dict[str, str]]:
        return parse_fact_items(self.facts_text)

    @property
    def form_title(self) -> str:
        return self.service_label or self.title


class Advantage(WebPImageMixin):
    ICON_PEN = "pen"
    ICON_BOX = "box"
    ICON_SPARK = "spark"
    ICON_CLOCK = "clock"

    ICON_CHOICES = (
        (ICON_PEN, "Перо"),
        (ICON_BOX, "Коробка"),
        (ICON_SPARK, "Искра"),
        (ICON_CLOCK, "Часы"),
    )

    order = models.PositiveIntegerField("Порядок", default=10)
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    icon = models.CharField("Иконка", max_length=32, choices=ICON_CHOICES, default=ICON_PEN)
    image = models.ImageField("Изображение", upload_to=advantage_image_upload_to, blank=True, null=True)
    image_alt = models.CharField("Описание изображения", max_length=255, blank=True)

    image_fields = ("image",)

    class Meta:
        verbose_name = "Преимущество"
        verbose_name_plural = "Преимущества"
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.title


class ProcessStep(models.Model):
    order = models.PositiveIntegerField("Порядок", default=10)
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Шаг"
        verbose_name_plural = "Шаги"
        ordering = ("order", "pk")

    def __str__(self) -> str:
        return self.title


class TelegramSubscriber(models.Model):
    chat_id = models.CharField("ID чата Telegram", max_length=128, unique=True)
    username = models.CharField("Имя пользователя", max_length=255, blank=True)
    first_name = models.CharField("Имя", max_length=255, blank=True)
    last_name = models.CharField("Фамилия", max_length=255, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    subscribed_at = models.DateTimeField("Подписан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Подписчик Telegram"
        verbose_name_plural = "Подписчики Telegram"
        ordering = ("-updated_at", "-pk")

    def __str__(self) -> str:
        label = self.username or " ".join(part for part in (self.first_name, self.last_name) if part).strip()
        return label or self.chat_id


class Application(models.Model):
    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_DONE = "done"
    STATUS_SPAM = "spam"

    STATUS_CHOICES = (
        (STATUS_NEW, "Новая"),
        (STATUS_CONTACTED, "В работе"),
        (STATUS_DONE, "Завершена"),
        (STATUS_SPAM, "Спам"),
    )

    name = models.CharField("Имя", max_length=255)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Электронная почта")
    service = models.ForeignKey(
        ServiceCard,
        on_delete=models.SET_NULL,
        related_name="applications",
        verbose_name="Услуга",
        blank=True,
        null=True,
    )
    service_name = models.CharField("Название услуги", max_length=255, blank=True)
    comment = models.TextField("Комментарий", blank=True)
    file = models.FileField(
        "Файл",
        upload_to=application_file_upload_to,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif", "pdf", "doc", "docx"])],
    )
    consent = models.BooleanField("Согласие", default=False)
    website = models.CharField("Антиспам-поле", max_length=255, blank=True)
    status = models.CharField("Статус", max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW)
    source_url = models.URLField("Источник", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ("-created_at", "-pk")

    def __str__(self) -> str:
        return f"{self.name} — {self.display_service}"

    @property
    def display_service(self) -> str:
        return self.service.title if self.service_id else self.service_name or "Другое"

    @property
    def service_display(self) -> str:
        return self.display_service

    def get_absolute_url(self) -> str:
        return reverse("admin:core_application_change", args=[self.pk])
