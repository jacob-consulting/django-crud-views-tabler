"""A fake courier API: tracking payloads derived deterministically from the shipped and delivered orders.

Everything but the clock is a function of the order: the tracking number and carrier come from the order number, the
event times are offsets from ``Order.shipped_at``, so two calls return the same payload.
"""

import random
from datetime import timedelta

from sales.models import Order, OrderState

CARRIERS = ["DHL", "DPD", "UPS", "GLS"]
# (description template, location, hours after shipping, icon); the first events always happen
EVENT_PLAN = [
    ("Shipment picked up at the roastery", "Acme Roasters, Bristol", 0, "picked-up"),
    ("Arrived at the origin parcel hub", "Bristol hub", 6, "in-transit"),
    ("Departed the origin hub", "Bristol hub", 20, "in-transit"),
    ("Out for delivery", "{city} depot", 52, "in-transit"),
    ("Delivered", "{city}", 58, "delivered"),
]
TRANSIT_SPREAD = 3  # days from shipping to the estimated delivery


def tracking_number(order_number: int) -> str:
    return f"ACME{order_number:08d}"


def carrier_for(order_number: int) -> str:
    return CARRIERS[order_number % len(CARRIERS)]


def _events(order: Order, delivered: bool) -> list[dict]:
    rng = random.Random(order.number)  # seeded by the order: the same events on every request
    shipped = order.shipped_at or order.created_at
    city = order.customer.city or "Destination"
    count = 5 if delivered else rng.randint(3, 4)
    events = []
    for description, location, hours, icon in EVENT_PLAN[:count]:
        events.append(
            {
                "at": shipped + timedelta(hours=hours + rng.randint(0, 3)),
                "description": description,
                "location": location.format(city=city),
                "icon": icon,
            }
        )
    return events


def fetch_shipments(orders=None) -> list[dict]:
    """One payload per shipped or delivered order, newest first; ``orders`` narrows the source queryset."""
    if orders is None:
        orders = Order.objects.all()
    orders = (
        orders.filter(state__in=[OrderState.SHIPPED, OrderState.DELIVERED])
        .select_related("customer")
        .order_by("-number")
    )
    payloads = []
    for order in orders:
        delivered = order.state == OrderState.DELIVERED
        shipped = order.shipped_at or order.created_at
        payloads.append(
            {
                "tracking_number": tracking_number(order.number),
                "order_number": order.number,
                "order_pk": order.pk,
                "customer_pk": order.customer_id,
                "customer_name": order.customer.name,
                "carrier": carrier_for(order.number),
                "status": "delivered" if delivered else "in_transit",
                "shipped_at": shipped,
                "eta": (shipped + timedelta(days=TRANSIT_SPREAD)).date(),
                "events": _events(order, delivered),
            }
        )
    return payloads
