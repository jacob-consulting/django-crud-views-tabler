import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

FIRST_NAMES = ["Jeffie", "Mallory", "Dunn", "Emmy", "Maryjo", "Egan", "Kellie", "Christabel", "Haskel", "Lorry",
               "Leesa", "Perren", "Sunny", "Geoffry", "Thatcher", "Dyann", "Avivah", "Kenon", "Nevil", "Rosalind"]
LAST_NAMES = ["Lewzey", "Hulme", "Slane", "Levet", "Lebarree", "Poajer", "Morrow", "Gaffney", "Mitchell", "Doble",
              "Ravens", "Breed", "Fenwick", "Ortega", "Varley", "Quinn", "Ashby", "Kemble", "Price", "Tarrant"]


class Command(BaseCommand):
    help = "Create demo users with sign-up and sign-in dates spread over the last year. They cannot log in."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=40)
        parser.add_argument("--seed", type=int, default=42, help="Random seed, for repeatable data.")

    def handle(self, *args, count, seed, **options):
        User = get_user_model()
        rng = random.Random(seed)
        now = timezone.now()
        created = 0
        for i in range(count):
            first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            username = f"demo-{first.lower()}-{last.lower()}-{i}"
            if User.objects.filter(username=username).exists():
                continue
            joined = now - timedelta(days=rng.randint(0, 364), hours=rng.randint(0, 23))
            user = User(
                username=username,
                first_name=first,
                last_name=last,
                email=f"{first.lower()}.{last.lower()}{i}@example.com",
                is_staff=rng.random() < 0.15,
                is_active=rng.random() < 0.9,
                date_joined=joined,
            )
            if rng.random() < 0.7:
                user.last_login = joined + (now - joined) * rng.random()
            user.set_unusable_password()
            user.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} demo user(s)."))
