"""Sales demo data: about 25 customers (cafés, shops and consumers) with addresses, Sam looking after some of them,
and about 70 orders over the last 90 days in every workflow state."""

import random
from datetime import timedelta

from catalog.models import Beans, Equipment, Product, Subscription
from crud_views_workflow.lib import run_transition
from crud_views_workflow.models import WorkflowInfo
from django.contrib.auth.models import Group, Permission
from django.utils import timezone

from .models import Address, Customer, CustomerSubscription, Order, OrderLine
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
    ("Mia Hoffmann", "Cologne", "DE"),
    ("Noah Schmidt", "Dresden", "DE"),
    ("Emma Fischer", "Bremen", "DE"),
    ("Ben Keller", "Graz", "AT"),
    ("Lea Wagner", "Hannover", "DE"),
    ("Finn Becker", "Basel", "CH"),
    ("Clara Vogel", "Utrecht", "NL"),
    ("Jakob Roth", "Salzburg", "AT"),
    ("Hanna Lorenz", "Hamburg", "DE"),
    ("Oskar Winter", "Malmö", "SE"),
    ("Ida Sommer", "Ghent", "BE"),
    ("Leon Arnold", "Stuttgart", "DE"),
    ("Mara Schulz", "Bern", "CH"),
]

STREETS = ["Hauptstraße", "Marktplatz", "Bahnhofstraße", "Gartenweg", "Rösterei-Allee", "Kaffeegasse", "Lindenstraße"]


def address(rng, customer, label, default):
    return Address(
        customer=customer,
        label=label,
        street=f"{rng.choice(STREETS)} {rng.randint(1, 120)}",
        zip_code=str(rng.randint(10000, 99999)),
        city=customer.city,
        country=customer.country,
        is_default=default,
    )


def seed(rng: random.Random, world: dict) -> None:
    users = world["users"]
    customers = []
    for name, contact, city, country, tier, terms, owner in WHOLESALE:
        slug = "".join(c for c in name.lower() if c.isalnum())
        customers.append(
            Customer.objects.create(
                name=name,
                kind="wholesale",
                contact_name=contact,
                email=f"orders@{slug}.example",
                phone=f"+{rng.randint(30, 49)} {rng.randint(100, 999)} {rng.randint(10000, 99999)}",
                city=city,
                country=country,
                owner=users.get(owner),
                company=name,
                vat_id=f"{country}{rng.randint(10**8, 10**9 - 1)}",
                price_tier=tier,
                payment_terms=terms,
                notes="Delivers on Tuesdays and Fridays." if rng.random() < 0.4 else "",
            )
        )
    for i, (name, city, country) in enumerate(CONSUMERS):
        first, last = name.lower().split()
        customers.append(
            Customer.objects.create(
                name=name,
                kind="consumer",
                contact_name=name,
                email=f"{first}.{last}@mail.example",
                city=city,
                country=country,
                owner=users["alex"] if i % 4 == 0 else None,
            )
        )

    addresses = []
    for customer in customers:
        labels = (
            ["Shop", "Billing"]
            if customer.is_wholesale and rng.random() < 0.6
            else ["Home" if not customer.is_wholesale else "Shop"]
        )
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
    # Orders: account managers view, add and change them (for their granted customers, via upstream's ancestor
    # guard) and take the workflow steps; Roasters only look, except that they mark confirmed orders as roasted.
    Group.objects.get(name="Account managers").permissions.add(
        perm("add_customer"),
        *(perm(f"{a}_address") for a in ("view", "add", "change", "delete")),
        *(perm(f"{a}_order") for a in ("view", "add", "change")),
        *(perm(f"{a}_customersubscription") for a in ("view", "add", "change")),  # for granted customers only
    )
    Group.objects.get(name="Roasters").permissions.add(
        perm("view_customer"),
        perm("view_address"),
        perm("view_order"),
        perm("roast_order"),
        perm("view_customersubscription"),
    )

    world["customers"] = customers
    world["orders"] = seed_orders(rng, customers, users)
    world["subscriptions"] = seed_subscriptions(rng, customers, world["products"])


ORDER_COUNT = 72
HISTORY_DAYS = 88

# state -> workflow steps taken from the draft (a cancelled order may have been confirmed first)
PATHS = {
    "draft": [],
    "confirmed": ["wf_confirm"],
    "roasted": ["wf_confirm", "wf_roast"],
    "shipped": ["wf_confirm", "wf_roast", "wf_ship"],
    "delivered": ["wf_confirm", "wf_roast", "wf_ship", "wf_deliver"],
    "cancelled": ["wf_cancel"],
    "cancelled after confirm": ["wf_confirm", "wf_cancel"],
}
# hours between an order and each step
STEP_HOURS = {"wf_confirm": 3, "wf_roast": 30, "wf_ship": 54, "wf_deliver": 100, "wf_cancel": 20}
# (oldest age in days, weights per PATHS key): older orders are mostly delivered, newer ones still in progress
STATE_MIX = [
    (35, {"delivered": 84, "cancelled": 6, "cancelled after confirm": 6, "shipped": 4}),
    (
        14,
        {"delivered": 35, "shipped": 25, "roasted": 15, "confirmed": 10, "cancelled": 5, "cancelled after confirm": 10},
    ),
    (5, {"delivered": 5, "shipped": 10, "roasted": 30, "confirmed": 35, "cancelled": 5, "draft": 15}),
    (0, {"shipped": 4, "roasted": 22, "confirmed": 38, "draft": 32, "cancelled": 4}),
]
# Orders by index (0 = oldest) with a fixed state, so every state is present whatever the dice say.
FORCED = {
    1: "cancelled",
    2: "delivered",
    ORDER_COUNT - 1: "draft",
    ORDER_COUNT - 2: "draft",
    ORDER_COUNT - 3: "confirmed",
    ORDER_COUNT - 4: "roasted",
    ORDER_COUNT - 5: "shipped",
}
COMMENTS = {"wf_cancel": "Customer changed their mind.", "wf_ship": "DHL, two parcels.", "wf_roast": ""}


def pick_path(rng: random.Random, age: int) -> list[str]:
    mix = next(weights for oldest, weights in STATE_MIX if age >= oldest)
    return PATHS[rng.choices(list(mix), weights=list(mix.values()))[0]]


def seed_orders(rng: random.Random, customers: list[Customer], users: dict) -> list[Order]:
    """``ORDER_COUNT`` orders spread over the last ``HISTORY_DAYS`` days, numbered by date; each has 1-4 lines."""
    products = list(Product.objects.instance_of(Beans, Equipment).filter(is_active=True))
    sams = [c for c in customers if c.owner == users["sam"]]
    others = [c for c in customers if c.owner != users["sam"]]
    now = timezone.now()
    plan = []
    for n in range(ORDER_COUNT):
        age = round(HISTORY_DAYS * (1 - n / (ORDER_COUNT - 1)) ** 1.25) + rng.randint(0, 1)
        created = now - timedelta(days=age, hours=rng.randint(0, 9))
        path = PATHS[FORCED[n]] if n in FORCED else pick_path(rng, age)
        by_sam = rng.random() < 0.4
        plan.append((created, rng.choice(sams if by_sam else others), users["sam" if by_sam else "alex"], path))
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
                order=order,
                product=product,
                quantity=rng.randint(1, 12) if beans else 1,
                grind=rng.choice(["whole", "filter", "espresso"]) if beans else "",
                bag_size=rng.choice(["250g", "1kg"]) if beans else "",
            )
        when = created
        for name in path:
            by = users["kim"] if name == "wf_roast" else seller
            when = min(when + timedelta(hours=STEP_HOURS[name]), now - timedelta(minutes=5))  # never in the future
            info = run_transition(order, name, user=by, comment=COMMENTS.get(name) or None)
            WorkflowInfo.objects.filter(pk=info.pk).update(timestamp=when)
            if name == "wf_ship":
                order.shipped_at = when
        Order.objects.filter(pk=order.pk).update(created_at=created, shipped_at=order.shipped_at)
        orders.append(order)
    return orders


# Days from today to the next delivery, one entry per subscription: some overdue, some due today, most ahead.
SUBSCRIPTION_OFFSETS = [-9, -4, -2, 0, 0, 1, 3, 5, 7, 9, 12, 16, 21, 27, 33, -6, 4]
PAUSED = {5, 12, 15}  # indexes into SUBSCRIPTION_OFFSETS


def seed_subscriptions(rng: random.Random, customers: list[Customer], products: list) -> list[CustomerSubscription]:
    """About 17 subscriptions (14 active), spread over Sam's customers and others, wholesale first."""
    plans = [p for p in products if isinstance(p, Subscription)]
    sams = [c for c in customers if c.owner and c.owner.username == "sam"]
    rest = [c for c in customers if c not in sams]
    pool = [*rng.sample(sams, min(5, len(sams))), *rng.sample(rest, min(12, len(rest)))]
    today = timezone.localdate()
    subs = []
    for n, (customer, offset) in enumerate(zip(pool, SUBSCRIPTION_OFFSETS, strict=False)):
        subs.append(
            CustomerSubscription.objects.create(
                customer=customer,
                product=rng.choice(plans),
                started_on=today - timedelta(days=rng.randint(40, 300)),
                next_delivery=today + timedelta(days=offset),
                is_active=n not in PAUSED,
            )
        )
    return subs
