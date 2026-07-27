from __future__ import annotations

import re

from django import forms

from core.models import Application, ServiceCard
from core.utils import clean_phone_number, format_phone_display

LINK_RE = re.compile(r"(https?://|www\.|t\.me/|max\.ru/)", re.IGNORECASE)
MAX_FILE_SIZE = 2 * 1024 * 1024


class ApplicationForm(forms.Form):
    name = forms.CharField(
        label="Ваше имя",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "id": "request-name",
                "autocomplete": "name",
                "required": "required",
            }
        ),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "id": "request-phone",
                "type": "tel",
                "inputmode": "tel",
                "autocomplete": "tel",
                "placeholder": "+7 (___) ___-__-__",
                "required": "required",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "id": "request-email",
                "autocomplete": "email",
                "required": "required",
            }
        ),
    )
    service = forms.ChoiceField(
        label="Интересующая услуга",
        choices=(),
        widget=forms.Select(
            attrs={
                "id": "request-service",
                "required": "required",
            }
        ),
    )
    service_name = forms.CharField(
        required=False,
        widget=forms.HiddenInput(
            attrs={
                "id": "request-service-name",
                "autocomplete": "off",
            }
        ),
    )
    comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(
            attrs={
                "id": "request-comment",
                "rows": 4,
                "placeholder": "Что вы хотите создать? Какие есть пожелания?",
            }
        ),
    )
    file = forms.FileField(
        label="Фото или макет",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "id": "request-file",
                "accept": "image/*,.pdf,.doc,.docx",
            }
        ),
    )
    consent = forms.BooleanField(
        required=True,
        initial=True,
        widget=forms.HiddenInput(attrs={"value": "1"}),
    )
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(
            attrs={
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

    def __init__(self, *args, service_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        services = list(service_queryset or ServiceCard.objects.order_by("order", "pk"))
        self.service_map = {str(service.pk): service for service in services}
        self.fields["service"].choices = [("", "Выберите услугу")] + [
            (str(service.pk), service.title) for service in services
        ] + [("other", "Другое")]

    def clean_name(self) -> str:
        name = " ".join((self.cleaned_data.get("name") or "").split())
        if len(name) < 2:
            raise forms.ValidationError("Укажите имя не короче 2 символов.")
        if len(name) > 255:
            raise forms.ValidationError("Имя слишком длинное.")
        if LINK_RE.search(name):
            raise forms.ValidationError("Имя заполнено некорректно.")
        return name

    def clean_phone(self) -> str:
        phone = clean_phone_number(self.cleaned_data.get("phone") or "")
        if not phone:
            raise forms.ValidationError("Укажите телефон в понятном формате.")
        return format_phone_display(phone)

    def clean_service_name(self) -> str:
        value = " ".join((self.cleaned_data.get("service_name") or "").split())
        if LINK_RE.search(value):
            raise forms.ValidationError("Название заполнено некорректно.")
        return value

    def clean_comment(self) -> str:
        comment = (self.cleaned_data.get("comment") or "").strip()
        if LINK_RE.search(comment):
            raise forms.ValidationError("Ссылки в комментарии запрещены.")
        return comment

    def clean_service(self):
        value = self.cleaned_data.get("service")
        if not value:
            raise forms.ValidationError("Выберите интересующую услугу.")
        if value == "other":
            return None
        service = self.service_map.get(str(value))
        if not service:
            raise forms.ValidationError("Выберите корректную услугу.")
        return service

    def clean_file(self):
        file_obj = self.cleaned_data.get("file")
        if file_obj and file_obj.size > MAX_FILE_SIZE:
            raise forms.ValidationError("Для демо-версии доступен файл до 2 МБ.")
        return file_obj

    def clean_website(self) -> str:
        value = (self.cleaned_data.get("website") or "").strip()
        if value:
            raise forms.ValidationError("Не удалось отправить заявку.")
        return value

    def clean_consent(self) -> bool:
        consent = bool(self.cleaned_data.get("consent"))
        if not consent:
            raise forms.ValidationError("Подтвердите согласие на обработку персональных данных.")
        return consent

    def save(self, *, source_url: str = "", commit: bool = True) -> Application:
        service = self.cleaned_data["service"]
        service_name = self.cleaned_data.get("service_name") or (service.title if service else "Другое")
        application = Application(
            name=self.cleaned_data["name"],
            phone=self.cleaned_data["phone"],
            email=self.cleaned_data["email"],
            service=service,
            service_name=service_name,
            comment=self.cleaned_data.get("comment", ""),
            file=self.cleaned_data.get("file"),
            consent=self.cleaned_data["consent"],
            website=self.cleaned_data.get("website", ""),
            source_url=source_url,
        )
        if commit:
            application.save()
        return application
