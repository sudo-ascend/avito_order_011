from __future__ import annotations

from django import template
from django.utils.html import format_html

from core.models import parse_fact_items
from core.utils import phone_href

register = template.Library()

ICON_PATHS = {
    "pen": "M6 24.5 22.8 7.7l1.5 1.5L7.5 26H6v-1.5ZM20.5 6l1.5-1.5 4 4L24.5 10M9.5 22.5l-3-3M12.5 19.5l-3-3",
    "box": "M8 8.5h16v15H8zM11 5.5h10M11 26.5h10M12 13h8M12 17h5",
    "spark": "M16 7v18M7 16h18M9.6 9.6l12.8 12.8M22.4 9.6 9.6 22.4",
    "clock": "M16 10v6l4 2.5M16 7a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z",
}


@register.simple_tag
def render_icon(name: str) -> str:
    path = ICON_PATHS.get(name, ICON_PATHS["pen"])
    return format_html('<svg viewBox="0 0 32 32" aria-hidden="true"><path d="{}"/></svg>', path)


@register.filter
def tel_href(value: str) -> str:
    return phone_href(value)


@register.filter
def split_lines(value: str) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


@register.filter
def split_facts(value: str):
    return parse_fact_items(value)
