"""Roastery demo data: green lots from real origins, cupping sessions scored by the team, roast batches.

Kim (head roaster) and Alex (owner) taste every session; Sam joins now and then. Batches fill the confirmed, roasted
and shipped orders. Beans in the catalog are linked to the lot they are roasted from. Kim may do everything in the
roastery; Sam only looks (Alex, as Owner, has every permission via dashboard's OWNER_APPS).
"""

import random
from datetime import timedelta
from decimal import Decimal

from catalog.models import Beans
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from sales.models import Order, OrderState

from .models import CuppingScore, CuppingSession, GreenLot, RoastBatch

# code, origin index (catalog seed ORIGINS), producer, variety, process, harvest, kg bought, kg on hand, €/kg,
# days ago, base score
LOTS = [
    (
        "CO-24-017",
        0,
        "Finca El Paraíso (Diego Bermúdez)",
        "Pink Bourbon",
        "washed",
        2024,
        "700",
        "690",
        "13.40",
        95,
        7.75,
    ),
    ("ET-24-003", 1, "Kochere washing station", "Heirloom", "natural", 2024, "450", "310", "12.10", 120, 8.0),
    ("KE-24-009", 2, "Gatomboya cooperative", "SL28, SL34", "washed", 2024, "300", "75", "14.80", 80, 7.75),
    ("BR-24-021", 3, "Fazenda Santa Luzia", "Yellow Catuaí", "natural", 2024, "1200", "880", "5.90", 140, 7.25),
    ("GT-23-005", 4, "Finca San Miguel", "Bourbon", "honey", 2023, "500", "40", "7.60", 260, 7.25),
    ("PE-24-012", 5, "Cooperativa Fortaleza del Valle", "Caturra", "washed", 2024, "600", "520", "6.80", 60, 7.0),
    ("ET-24-014", 1, "Daye Bensa", "Heirloom", "anaerobic", 2024, "200", "130", "21.50", 45, 8.25),
]

TASTERS_BY_SESSION = [("alex", "kim"), ("kim", "alex", "sam"), ("alex", "kim"), ("kim", "sam")]
NOTES = [
    "",
    "Sweet, clean cup; the acidity opens as it cools.",
    "Slightly papery at the start.",
    "Resubmit after resting a week.",
]

BATCHES = 30

# lot index -> profile for its batches
PROFILES = {0: "light", 1: "light", 2: "medium", 3: "espresso", 4: "medium", 5: "dark", 6: "light"}


def snap(value: float) -> Decimal:
    """Round to the nearest quarter point, within 0 to 10."""
    return Decimal(str(min(10.0, max(0.0, round(value * 4) / 4))))


def seed(rng: random.Random, world: dict) -> None:
    users = world["users"]
    origins = world["origins"]
    today = timezone.localdate()

    lots = []
    on_hand_after = {}  # the stock each lot should show once the batches below have drawn theirs
    for code, o, producer, variety, process, year, bought, on_hand, price, days, base in LOTS:
        lots.append(
            (
                GreenLot.objects.create(
                    code=code,
                    origin=origins[o],
                    producer=producer,
                    variety=variety,
                    process=process,
                    harvest_year=year,
                    kg_purchased=Decimal(bought),
                    kg_on_hand=Decimal(bought),
                    price_per_kg=Decimal(price),
                    arrived_on=today - timedelta(days=days),
                ),
                base,
            )
        )
        on_hand_after[code] = Decimal(on_hand)

    sessions = []
    for n, (lot, base) in enumerate(lots):
        for s in range(2 if n % 3 else 3):
            session = CuppingSession.objects.create(
                lot=lot, held_on=lot.arrived_on + timedelta(days=7 + s * 9 + n), notes=rng.choice(NOTES)
            )
            for taster in TASTERS_BY_SESSION[(n + s) % len(TASTERS_BY_SESSION)]:
                CuppingScore.objects.create(
                    session=session,
                    taster=users[taster],
                    **{name: snap(base + rng.uniform(-0.5, 0.75)) for name in CuppingScore.ATTRIBUTES},
                )
            sessions.append(session)

    # beans in the catalog are roasted from the lot with their origin (and process, when there is one)
    all_lots = [lot for lot, _ in lots]
    for beans in Beans.objects.all():
        same_origin = [lot for lot in all_lots if lot.origin_id == beans.origin_id]
        match = [lot for lot in same_origin if lot.process == beans.process] or same_origin
        if match:
            beans.green_lot = match[0]
            beans.save(update_fields=["green_lot"])

    # batches: older ones fill shipped orders, recent ones the confirmed and roasted orders
    open_orders = list(Order.objects.filter(state__in=[OrderState.CONFIRMED, OrderState.ROASTED]).order_by("number"))
    done_orders = list(Order.objects.filter(state__in=[OrderState.SHIPPED, OrderState.DELIVERED]).order_by("number"))
    batches = []
    for n in range(BATCHES):
        lot_index = n % len(lots)
        lot = lots[lot_index][0]
        green = Decimal(rng.choice([8, 10, 12, 12, 15, 15, 20]))
        loss = Decimal(str(round(rng.uniform(0.12, 0.17), 3)))
        batch = RoastBatch.objects.create(
            lot=lot,
            roasted_on=today - timedelta(days=(BATCHES - n) * 2 + rng.randint(0, 1)),
            profile=PROFILES[lot_index],
            green_kg=green,
            roasted_kg=(green * (1 - loss)).quantize(Decimal("0.1")),
            roaster=users["kim"] if n % 4 else users["alex"],
        )
        pool = open_orders if n >= BATCHES * 2 // 3 else done_orders
        if pool:
            batch.orders.set(rng.sample(pool, min(len(pool), rng.randint(0, 2))))
        batches.append(batch)

    # batches draw from the lots (RoastBatch.save): lots start full and end at the stated stock, or at what the batches
    # left of them when that is less
    for lot, _ in lots:
        lot.refresh_from_db()
        lot.kg_on_hand = min(lot.kg_on_hand, on_hand_after[lot.code])
        lot.save(update_fields=["kg_on_hand"])

    # Kim runs the roastery; Sam looks, and gives cupping scores (he may not edit anything here)
    perms = Permission.objects.filter(content_type__app_label="roastery")
    Group.objects.get(name="Roasters").permissions.add(*perms)
    Group.objects.get(name="Account managers").permissions.add(*perms.filter(codename__startswith="view_"))

    world["lots"] = all_lots
    world["cupping_sessions"] = sessions
    world["batches"] = batches
