"""Sales demo data: about 25 customers (cafés, shops and consumers) with addresses, Sam looking after some of them,
and a few orders in every workflow state (Task 10 grows the full world)."""

import random
from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.utils import timezone

from catalog.models import Beans, Equipment, Product

from .models import Address, Customer, Order, OrderLine
from .permissions import grant_customer
from .workflow import run_transition

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
    # Orders: account managers view, add and change them (for their granted customers, see CustomerGrantMixin) and
    # take the workflow steps; Roasters only look, except that they mark confirmed orders as roasted.
    Group.objects.get(name="Account managers").permissions.add(
        perm("add_customer"),
        *(perm(f"{a}_address") for a in ("view", "add", "change", "delete")),
        *(perm(f"{a}_order") for a in ("view", "add", "change")),
    )
    Group.objects.get(name="Roasters").permissions.add(
        perm("view_customer"), perm("view_address"), perm("view_order"), perm("roast_order")
    )

    world["customers"] = customers
    world["orders"] = seed_orders(rng, customers, users)


# How far each seeded order got along the happy path (or cancelled after the draft), oldest first.
ORDER_PATHS = [
    ["wf_confirm", "wf_roast", "wf_ship", "wf_deliver"],
    ["wf_confirm", "wf_roast", "wf_ship", "wf_deliver"],
    ["wf_confirm", "wf_roast", "wf_ship", "wf_deliver"],
    ["wf_cancel"],
    ["wf_confirm", "wf_roast", "wf_ship"],
    ["wf_confirm", "wf_roast", "wf_ship"],
    ["wf_confirm", "wf_cancel"],
    ["wf_confirm", "wf_roast"],
    ["wf_confirm", "wf_roast"],
    ["wf_confirm", "wf_roast"],
    ["wf_confirm"],
    ["wf_confirm"],
    ["wf_confirm"],
    [],
    [],
    [],
]
COMMENTS = {"wf_cancel": "Customer changed their mind.", "wf_ship": "DHL, two parcels.", "wf_roast": ""}


def seed_orders(rng: random.Random, customers: list[Customer], users: dict) -> list[Order]:
    """``ORDER_PATHS`` twice, for Sam's customers and for the rest, numbered by date; each order has 1-4 lines."""
    products = list(Product.objects.instance_of(Beans, Equipment).filter(is_active=True))
    sams = [c for c in customers if c.owner == users["sam"]]
    others = [c for c in customers if c.owner != users["sam"]]
    now = timezone.now()
    plan = []
    for pool, seller in ((sams, users["sam"]), (others, users["alex"])):
        for n, path in enumerate(ORDER_PATHS):
            created = now - timedelta(days=(len(ORDER_PATHS) - n) * 3 + rng.randint(0, 2), hours=rng.randint(1, 8))
            plan.append((created, rng.choice(pool), seller, path))
    orders = []
    for created, customer, seller, path in sorted(plan, key=lambda p: p[0]):  # order numbers follow the dates
        order = Order.objects.create(
            customer=customer,
            ship_to=customer.addresses.filter(is_default=True).first(),
            requested_roast_date=(created + timedelta(days=rng.randint(2, 6))).date(),
            notes="Please label the bags with the café logo." if rng.random() < 0.2 else "",
        )
        for product in rng.sample(products, rng.randint(1, 4)):
            beans = isinstance(product, Beans)
            OrderLine.objects.create(
                order=order, product=product, quantity=rng.randint(1, 12) if beans else 1,
                grind=rng.choice(["whole", "filter", "espresso"]) if beans else "",
                bag_size=rng.choice(["250g", "1kg"]) if beans else "",
            )
        for step, name in enumerate(path, 1):
            by = users["kim"] if name == "wf_roast" else seller
            when = created + timedelta(days=step, hours=step)
            run_transition(order, name, by, comment=COMMENTS.get(name) or None, when=when)
            if name == "wf_ship":
                order.shipped_at = when
        Order.objects.filter(pk=order.pk).update(created_at=created, shipped_at=order.shipped_at)
        orders.append(order)
    return orders
