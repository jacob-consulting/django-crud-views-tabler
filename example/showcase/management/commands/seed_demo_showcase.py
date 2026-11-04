import random
from datetime import time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from showcase.models import ShowcaseCategory, ShowcaseChannel, ShowcaseItem, ShowcaseTag

CATEGORIES = ["Audio", "Cables", "Displays", "Keyboards", "Storage"]
TAGS = ["bestseller", "clearance", "eco", "fragile", "new", "refurbished"]
CHANNELS = ["Online shop", "Resellers", "Retail stores", "Wholesale"]
NOUNS = ["Adapter", "Dock", "Hub", "Keyboard", "Monitor", "Mouse", "Speaker", "SSD", "Switch", "Webcam"]
ADJECTIVES = ["Compact", "Dual", "Mini", "Pro", "Quiet", "Rugged", "Slim", "Studio", "Ultra", "Wireless"]
COLORS = ["#066fd1", "#2fb344", "#d63939", "#f76707", "#ae3ec9", "#4299e1"]


class Command(BaseCommand):
    help = "Create demo products, categories, tags and channels for the crispy/Tabler form coverage page."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=40)
        parser.add_argument("--seed", type=int, default=11, help="Random seed, for repeatable data.")

    def handle(self, *args, count, seed, **options):
        rng = random.Random(seed)
        categories = [ShowcaseCategory.objects.get_or_create(name=name)[0] for name in CATEGORIES]
        tags = [ShowcaseTag.objects.get_or_create(name=name)[0] for name in TAGS]
        channels = [ShowcaseChannel.objects.get_or_create(name=name)[0] for name in CHANNELS]
        now = timezone.now()
        created = 0
        for i in range(count):
            name = f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)} {i + 1}"
            slug = name.lower().replace(" ", "-")
            if ShowcaseItem.objects.filter(slug=slug).exists():
                continue
            product = ShowcaseItem.objects.create(
                name=name,
                slug=slug,
                description=f"A {name.lower()} for the crispy form coverage demo.",
                category=rng.choice(categories),
                size=rng.choice(list(ShowcaseItem.Size)),
                shipping=rng.choice(list(ShowcaseItem.Shipping)),
                price=Decimal(rng.randrange(500, 150_000)) / 100,
                warranty_months=rng.choice([12, 24, 36]),
                stock=rng.choices([0, rng.randint(1, 9), rng.randint(10, 400)], weights=[1, 2, 7])[0],
                rating=rng.randint(1, 5),
                released_on=(now - timedelta(days=rng.randint(0, 900))).date(),
                published_at=now - timedelta(days=rng.randint(0, 400), hours=rng.randint(0, 23)),
                restock_at=time(hour=rng.choice([6, 9, 14, 18]), minute=rng.choice([0, 15, 30])),
                is_active=rng.random() < 0.85,
                is_featured=rng.random() < 0.2,
                accent_color=rng.choice(COLORS),
                contact_email=f"sales{i}@example.com",
                website=f"https://example.com/products/{slug}",
            )
            product.tags.set(rng.sample(tags, rng.randint(0, 3)))
            product.channels.set(rng.sample(channels, rng.randint(1, 3)))
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} demo product(s)."))
