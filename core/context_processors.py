from core.models import HomePageSettings, SiteSettings


def site_context(request):
    return {
        "site_settings": SiteSettings.get_solo(),
        "home_settings": HomePageSettings.get_solo(),
    }
