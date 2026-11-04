"""Sales demo data: about 25 customers (cafés, shops and consumers) with addresses; Sam looks after some of them."""

import random

from django.contrib.auth.models import Group, Permission

from .models import Address, Customer
from .permissions import grant_customer

# name, kind, contact, city, country, tier, terms, owner
WHOLESALE = [
    ("Bean & Bloom Café", "Jonas Weber", "Hamburg", "DE", "B", "net_30", "sam"),
    ("Kaffeehaus Lindenhof", "Marta Klein", "Vienna", "AT", "A", "net_30", "sam"),
    ("Quiet Corner Roasters", "Tom Hale", "Bristol", "GB", "C", "net_14", "sam"),
    ("Café Rue Mouffe", "Claire Fontaine", "Paris", "FR", "B", "net_30", "sam"),
    ("Fika & Friends", "Elin Berg", "Gothenburg", "SE", "B", "net_60", "alex"),
    ("The Daily Grind", "Sophie Turner", "Leeds", "GB", "C", "prepaid", "alex"),
    ("Bohne 7", "Lukas Brandt", "Berlin", "DE", "A", "net_30", None),
    ("Espresso Bar Navigli", "Giulia Rossi", "Milan", "IT", "B", "net_30", None),
    ("Marktstand Meier", "Hans Meier", "Munich", "DE", "C", "prepaid", "alex"),
    ("Hotel Seeblick", "Anna Gruber", "Zurich", "CH", "A", "net_60", "alex"),
    ("Bücherstube & Kaffee", "Paul Neumann", "Leipzig", "DE", "C", "net_14", None),
    ("Roest Amsterdam", "Daan de Vries", "Amsterdam", "NL", "B", "net_30", None),
]

CONSUMERS = [
    ("Mia Hoffmann", "Cologne", "DE"), ("Noah Schmidt", "Dresden", "DE"), ("Emma Fischer", "Bremen", "DE"),
    ("Ben Keller", "Graz", "AT"), ("Lea Wagner", "Hannover", "DE"), ("Finn Becker", "Basel", "CH"),
    ("Clara Vogel", "Utrecht", "NL"), ("Jakob Roth", "Salzburg", "AT"), ("Hanna Lorenz", "Hamburg", "DE"),
    ("Oskar Winter", "Malmö", "SE"), ("Ida Sommer", "Ghent", "BE"), ("Leon Arnold", "Stuttgart", "DE"),
    ("Mara Schulz", "Bern", "CH"),
]

STREETS = ["Hauptstraße", "Marktplatz", "Bahnhofstraße", "Gartenweg", "Rösterei-Allee", "Kaffeegasse", "Lindenstraße"]


def address(rng, customer, label, default):
    return Address(
        customer=customer, label=label, street=f"{rng.choice(STREETS)} {rng.randint(1, 120)}",
        zip_code=str(rng.randint(10000, 99999)), city=customer.city, country=customer.country, is_default=default,
    )


def seed(rng: random.Random, world: dict) -> None:
    users = world["users"]
    customers = []
    for name, contact, city, country, tier, terms, owner in WHOLESALE:
        slug = "".join(c for c in name.lower() if c.isalnum())
        customers.append(Customer.objects.create(
            name=name, kind="wholesale", contact_name=contact, email=f"orders@{slug}.example",
            phone=f"+{rng.randint(30, 49)} {rng.randint(100, 999)} {rng.randint(10000, 99999)}", city=city,
            country=country, owner=users.get(owner), company=name, vat_id=f"{country}{rng.randint(10**8, 10**9 - 1)}",
            price_tier=tier, payment_terms=terms,
            notes="Delivers on Tuesdays and Fridays." if rng.random() < 0.4 else "",
        ))
    for i, (name, city, country) in enumerate(CONSUMERS):
        first, last = name.lower().split()
        customers.append(Customer.objects.create(
            name=name, kind="consumer", contact_name=name, email=f"{first}.{last}@mail.example", city=city,
            country=country, owner=users["alex"] if i % 4 == 0 else None,
        ))

    addresses = []
    for customer in customers:
        labels = ["Shop", "Billing"] if customer.is_wholesale and rng.random() < 0.6 else ["Home" if not customer.is_wholesale else "Shop"]
        addresses += [address(rng, customer, label, n == 0) for n, label in enumerate(labels)]
    Address.objects.bulk_create(addresses)

    # Sam sees exactly the customers granted to Sam; Alex, as Owner, has every permission model-wide
    for customer in customers:
        if customer.owner == users["sam"]:
            grant_customer(users["sam"], customer)

    # Account managers may add customers (and then see the ones they created or were granted) and manage the
    # addresses of those; they get no model-level view permission on customers, or Guardian's object check would be
    # bypassed. Roasters (Kim) may look at customers and addresses, not edit.
    perm = lambda codename: Permission.objects.get(content_type__app_label="sales", codename=codename)  # noqa: E731
    Group.objects.get(name="Account managers").permissions.add(
        perm("add_customer"), *(perm(f"{a}_address") for a in ("view", "add", "change", "delete"))
    )
    Group.objects.get(name="Roasters").permissions.add(perm("view_customer"), perm("view_address"))

    world["customers"] = customers
