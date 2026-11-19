"""Catalog demo data: categories, origins, flavor notes and a mix of beans, equipment and subscriptions."""

import random
from decimal import Decimal

from django.contrib.auth.models import Group, Permission
from django.utils.text import slugify

from .models import Beans, Category, Equipment, FlavorNote, Origin, Product, Subscription

CATEGORIES = ["Single origin", "Blends", "Equipment", "Subscriptions"]

ORIGINS = [
    ("CO", "Huila"),
    ("ET", "Yirgacheffe"),
    ("KE", "Nyeri"),
    ("BR", "Cerrado"),
    ("GT", "Antigua"),
    ("PE", "Cajamarca"),
    ("GT", "Huehuetenango"),
    ("CR", "Tarrazú"),
    ("RW", "Nyamasheke"),
]

NOTES = {
    "raspberry": "red",
    "rose": "pink",
    "cane sugar": "orange",
    "jasmine": "lime",
    "bergamot": "yellow",
    "blueberry": "indigo",
    "cocoa": "brown",
    "hazelnut": "orange",
    "black tea": "azure",
    "red apple": "red",
    "caramel": "orange",
    "citrus": "yellow",
    "plum": "purple",
    "peach": "pink",
    "honey": "yellow",
    "almond": "brown",
    "orange": "orange",
    "dark chocolate": "brown",
}

# name, origin index, process, altitude, roast, notes, price, stock, active
BEANS = [
    ("Huila Pink Bourbon", 0, "washed", 1750, "light", ["raspberry", "rose", "cane sugar"], "16.50", 42, True),
    ("Yirgacheffe Kochere", 1, "natural", 1900, "light", ["blueberry", "jasmine", "bergamot"], "17.90", 28, True),
    ("Nyeri AA", 2, "washed", 1700, "medium", ["black tea", "citrus", "red apple"], "16.00", 6, True),
    ("Cerrado Natural", 3, "natural", 1100, "medium", ["cocoa", "hazelnut", "caramel"], "12.80", 80, True),
    ("Antigua Honey", 4, "honey", 1500, "medium", ["caramel", "cocoa", "red apple"], "13.90", 35, True),
    ("Cajamarca Dark", 5, "washed", 1650, "dark", ["cocoa", "hazelnut"], "12.50", 0, True),
    ("Yirgacheffe Anaerobic", 1, "anaerobic", 2000, "light", ["jasmine", "raspberry", "bergamot"], "22.00", 12, True),
    (
        "Huehuetenango Washed",
        6,
        "washed",
        1800,
        "medium",
        ["caramel", "dark chocolate", "red apple"],
        "14.50",
        33,
        True,
    ),
    ("Tarrazú Honey", 7, "honey", 1600, "medium", ["honey", "orange", "cane sugar"], "15.40", 21, True),
    ("Nyamasheke Bourbon", 8, "washed", 1850, "light", ["plum", "black tea", "citrus"], "16.80", 17, True),
    ("Nyeri Peaberry", 2, "washed", 1750, "light", ["red apple", "black tea", "citrus"], "19.50", 9, True),
    ("House Espresso Blend", 3, "natural", 1050, "dark", ["dark chocolate", "caramel", "almond"], "11.90", 120, True),
    ("Sunrise Filter Blend", 0, "washed", 1600, "medium", ["peach", "honey", "citrus"], "13.20", 54, True),
    ("Decaf Huila", 0, "washed", 1650, "medium", ["caramel", "cocoa"], "15.00", 8, True),
    ("Huila Estate (retired)", 0, "washed", 1650, "medium", ["caramel", "citrus"], "14.20", 3, False),
]

# name, brand, warranty months, weight kg, price, stock
EQUIPMENT = [
    ("C40 MK4 hand grinder", "Comandante", 24, "0.73", "289.00", 3),
    ("V60 02 dripper", "Hario", 12, "0.20", "28.00", 40),
    ("Gooseneck kettle", "Fellow", 24, "0.85", "119.00", 14),
    ("Precision scale", "Acaia", 12, "0.40", "149.00", 9),
    ("Hand grinder Q2", "1Zpresso", 24, "0.60", "99.00", 0),
    ("Chemex 6-cup", "Chemex", 12, "0.45", "52.00", 18),
    ("Moka Express 3-cup", "Bialetti", 24, "0.35", "34.00", 26),
    ("AeroPress Go", "AeroPress", 12, "0.31", "39.00", 22),
    ("Timemore C2 grinder", "Timemore", 24, "0.54", "79.00", 7),
    ("Distribution tool", "Normcore", 12, "0.15", "24.00", 31),
]

# name, interval, bags, size, price
SUBSCRIPTIONS = [
    ("Roaster’s choice", "biweekly", 2, "250g", "29.00"),
    ("Espresso club", "monthly", 4, "250g", "52.00"),
    ("Office pack", "weekly", 2, "1kg", "76.00"),
    ("Decaf duo", "monthly", 2, "250g", "27.00"),
    ("Filter lover", "biweekly", 3, "250g", "41.00"),
]

# Permission codenames for the two non-owner groups; Owner gets everything via dashboard's OWNER_APPS.
VIEW_ONLY_GROUPS = ("Account managers", "Roasters")


def seed(rng: random.Random, world: dict) -> None:
    categories = {name: Category.objects.create(name=name) for name in CATEGORIES}
    origins = [Origin.objects.create(country=c, region=r) for c, r in ORIGINS]
    notes = {name: FlavorNote.objects.create(name=name, color=color) for name, color in NOTES.items()}
    products: list[Product] = []

    for n, (name, o, process, alt, roast, flavor, price, stock, active) in enumerate(BEANS, 1):
        beans = Beans.objects.create(
            name=name,
            slug=slugify(name),
            sku=f"BN-{n:03d}",
            price=Decimal(price),
            stock=stock,
            is_active=active,
            category=categories["Blends" if "blend" in name.lower() else "Single origin"],
            origin=origins[o],
            process=process,
            altitude_m=alt,
            roast_level=roast,
            description=f"{name}: {', '.join(flavor)}. Roasted {roast} for filter and espresso.",
        )
        beans.flavor_notes.set([notes[f] for f in flavor])
        products.append(beans)
    for n, (name, brand, warranty, weight, price, stock) in enumerate(EQUIPMENT, 1):
        products.append(
            Equipment.objects.create(
                name=name,
                slug=slugify(name),
                sku=f"EQ-{n:03d}",
                price=Decimal(price),
                stock=stock,
                category=categories["Equipment"],
                brand=brand,
                warranty_months=warranty,
                weight_kg=Decimal(weight),
                description=f"{brand} {name.lower()}.",
            )
        )
    for n, (name, interval, bags, size, price) in enumerate(SUBSCRIPTIONS, 1):
        products.append(
            Subscription.objects.create(
                name=name,
                slug=slugify(name),
                sku=f"SU-{n:03d}",
                price=Decimal(price),
                category=categories["Subscriptions"],
                interval=interval,
                bags_per_delivery=bags,
                bag_size=size,
                description="Fresh coffee on a schedule; pause or cancel any time.",
            )
        )

    # Account managers and Roasters look at the catalog but never change it (Owner has every permission).
    view_perms = Permission.objects.filter(content_type__app_label="catalog", codename__startswith="view_")
    for group in Group.objects.filter(name__in=VIEW_ONLY_GROUPS):
        group.permissions.add(*view_perms)

    world["categories"] = list(categories.values())
    world["origins"] = origins
    world["flavor_notes"] = list(notes.values())
    world["products"] = products
