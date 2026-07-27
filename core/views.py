from __future__ import annotations

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from core.forms import ApplicationForm
from core.models import Advantage, HomePageSettings, ProcessStep, ProductRow, ServiceCard, SiteSettings
from core.seed import ensure_default_content


def home(request):
    if request.method == "POST":
        from core.api import submit_application

        return submit_application(request)

    ensure_default_content()
    site_settings = SiteSettings.get_solo()
    home_settings = HomePageSettings.get_solo()
    services = list(ServiceCard.objects.order_by("order", "pk"))
    products = list(ProductRow.objects.order_by("order", "pk"))
    advantages = list(Advantage.objects.order_by("order", "pk"))
    steps = list(ProcessStep.objects.order_by("order", "pk"))
    gift_service = next((service for service in services if service.title == "Фотопостеры"), services[0] if services else None)
    form = ApplicationForm(initial={"service": str(gift_service.pk) if gift_service else ""}, service_queryset=services)
    return render(
        request,
        "home.html",
        {
            "site_settings": site_settings,
            "home_settings": home_settings,
            "services": services,
            "products": products,
            "advantages": advantages,
            "steps": steps,
            "gift_service": gift_service,
            "form": form,
            "body_class": "page page--home",
        },
    )


def robots_txt(request):
    return HttpResponse("User-agent: *\nAllow: /\n", content_type="text/plain; charset=utf-8")


def csrf_failure(request, reason=""):
    return render(request, "error_pages/403_csrf.html", status=403, context={"reason": reason})


def json_error(message: str, status: int = 400):
    return JsonResponse({"success": False, "message": message}, status=status)
