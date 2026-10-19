import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from customers.models import Customer

NAMES = ["Jeffie Lewzey", "Mallory Hulme", "Dunn Slane", "Emmy Levet", "Maryjo Lebarree", "Egan Poajer",
         "Kellie Morrow", "Christabel Gaffney", "Haskel Mitchell", "Lorry Doble", "Leesa Ravens", "Perren Breed",
         "Sunny Fenwick", "Geoffry Ortega", "Thatcher Varley", "Dyann Quinn", "Avivah Ashby", "Kenon Kemble",
         "Nevil Price", "Rosalind Tarrant"]
COMPANIES = ["Northwind", "Contoso", "Fabrikam", "Initech", "Globex", "Umbrella", "Hooli", "Vandelay", "", ""]
COUNTRIES = ["Germany", "Austria", "Switzerland", "France", "Netherlands", "Poland", "Spain", "Italy"]


class Command(BaseCommand):
    help = "Create demo customers for the crud_views Tabler prototype."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=60)
        parser.add_argument("--seed", type=int, default=7, help="Random seed, for repeatable data.")

    def handle(self, *args, count, seed, **options):
        rng = random.Random(seed)
        customers = []
        for i in range(count):
            name = rng.choice(NAMES)
            first = name.split()[0].lower()
            customers.append(Customer(
                name=f"{name} {i}" if i >= len(NAMES) else name,
                company=rng.choice(COMPANIES),
                email=f"{first}{i}@example.com",
                country=rng.choice(COUNTRIES),
                status=rng.choices(list(Customer.Status), weights=[3, 5, 2])[0],
                revenue=Decimal(rng.randrange(0, 250_000_00)) / 100,
            ))
        Customer.objects.bulk_create(customers)
        self.stdout.write(self.style.SUCCESS(f"Created {len(customers)} demo customer(s)."))
