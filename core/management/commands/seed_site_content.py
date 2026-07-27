from django.core.management.base import BaseCommand

from core.seed import ensure_default_content, sync_site_content


class Command(BaseCommand):
    help = "Fill the database with the default site content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Update existing content records to match the current site content and attach bundled images.",
        )

    def handle(self, *args, **options):
        if options["sync"]:
            sync_site_content()
            self.stdout.write(self.style.SUCCESS("Site content synchronized."))
            return

        ensure_default_content()
        self.stdout.write(self.style.SUCCESS("Site content seeded."))
