from __future__ import annotations

from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile

from core.default_content import (
    ADVANTAGES,
    HOME_FILE_DEFAULTS,
    HOME_SETTINGS_DEFAULTS,
    PROCESS_STEPS,
    PRODUCT_ROWS,
    SERVICE_CARDS,
    SITE_FILE_DEFAULTS,
    SITE_SETTINGS_DEFAULTS,
)
from core.models import Advantage, HomePageSettings, ProcessStep, ProductRow, ServiceCard, SiteSettings


def _load_asset_content(path: str) -> tuple[str | None, ContentFile | None]:
    file_path = Path(settings.BASE_DIR) / path
    if not file_path.exists():
        return None, None
    return file_path.name, ContentFile(file_path.read_bytes())


def _is_empty(value: Any) -> bool:
    return value is None or value == ""


def _attach_file(instance, field_name: str, path: str, *, overwrite: bool = False) -> bool:
    name, content = _load_asset_content(path)
    if not name or not content:
        return False

    field = getattr(instance, field_name)
    current_name = Path(field.name).name if field and getattr(field, "name", "") else ""
    if current_name == name:
        return False
    if current_name and not overwrite:
        return False

    field.save(name, content, save=False)
    return True


def _apply_values(instance, values: dict[str, Any], *, overwrite: bool = False) -> bool:
    changed = False
    for field_name, value in values.items():
        current = getattr(instance, field_name)
        if not overwrite and not _is_empty(current):
            continue
        if _is_empty(value) and not _is_empty(current):
            continue
        if current != value:
            setattr(instance, field_name, value)
            changed = True
    return changed


def _sync_singleton(instance, values: dict[str, Any], files: dict[str, str], *, overwrite: bool = False) -> None:
    changed = _apply_values(instance, values, overwrite=overwrite)
    for field_name, path in files.items():
        changed = _attach_file(instance, field_name, path, overwrite=overwrite) or changed
    if changed:
        instance.save()


def _sync_ordered_model(model, items: list[dict[str, Any]], *, image_field: str | None = "image", overwrite: bool = False) -> None:
    existing_by_order = {}
    for obj in model.objects.order_by("order", "pk"):
        existing_by_order.setdefault(obj.order, obj)

    for item in items:
        obj = existing_by_order.get(item["order"]) or model(order=item["order"])
        field_values = {key: value for key, value in item.items() if key != image_field}
        changed = _apply_values(obj, field_values, overwrite=overwrite)

        if image_field and item.get(image_field):
            changed = _attach_file(obj, image_field, item[image_field], overwrite=overwrite) or changed

        if obj.pk is None or changed:
            obj.save()


def _sync_site_content(*, overwrite: bool) -> None:
    site = SiteSettings.get_solo()
    _sync_singleton(site, SITE_SETTINGS_DEFAULTS, SITE_FILE_DEFAULTS, overwrite=overwrite)

    home = HomePageSettings.get_solo()
    _sync_singleton(home, HOME_SETTINGS_DEFAULTS, HOME_FILE_DEFAULTS, overwrite=overwrite)

    _sync_ordered_model(ServiceCard, SERVICE_CARDS, overwrite=overwrite)
    _sync_ordered_model(ProductRow, PRODUCT_ROWS, overwrite=overwrite)
    _sync_ordered_model(Advantage, ADVANTAGES, overwrite=overwrite)
    _sync_ordered_model(ProcessStep, PROCESS_STEPS, image_field=None, overwrite=overwrite)


def ensure_default_content() -> None:
    _sync_site_content(overwrite=False)


def sync_site_content() -> None:
    _sync_site_content(overwrite=True)
