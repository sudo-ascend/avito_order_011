from django.contrib.sitemaps.views import sitemap
from django.urls import path

from core import api, views
from core.sitemaps import HomeSitemap

sitemaps = {"home": HomeSitemap}

urlpatterns = [
    path("", views.home, name="home"),
    path("api/application/", api.submit_application, name="submit_application"),
    path("api/telegram/<str:token>/", api.TelegramWebhookApiView.as_view(), name="telegram_webhook_api"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]
