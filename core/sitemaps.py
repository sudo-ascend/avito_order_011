from django.urls import reverse
from django.contrib.sitemaps import Sitemap


class HomeSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return [None]

    def location(self, item):
        return reverse("home")
