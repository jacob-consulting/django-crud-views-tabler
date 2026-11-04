import random
from importlib import import_module

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

# Each app listed here has a ``seed.py`` with ``seed(rng, world)``. Later apps append themselves, in dependency order.
SEED_APPS = ["dashboard", "catalog", "sales", "roastery"]

DEMO_USERNAMES = ("alex", "sam", "kim")


class Command(BaseCommand):
    help = "Seed the Acme Roasters demo data (demo accounts alex, sam, kim; password demo)."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Random seed, for repeatable data.")

    def handle(self, *args, seed, **options):
        User = get_user_model()
        if User.objects.filter(username__in=DEMO_USERNAMES).exists():
            self.stdout.write("The demo data already exists (users alex, sam or kim); nothing was changed.")
            return
        rng = random.Random(seed)
        world: dict = {}
        with transaction.atomic():
            for app in SEED_APPS:
                import_module(f"{app}.seed").seed(rng, world)
        self.stdout.write(self.style.SUCCESS(f"Seeded the demo data for: {', '.join(SEED_APPS)}."))
