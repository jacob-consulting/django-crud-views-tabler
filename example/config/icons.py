"""The Acme app's icon vocabulary: domain meaning -> Tabler icon name.

App code, templates and seed data name icons by what they stand for (``"customer"``, ``"order"``), never by picture or
library. This table is the only place that knows the library: ``settings.py`` feeds it to ``CRUD_VIEWS_ICONS`` (for
django-crud-views, as ``tabler:<name>``) and to ``TABLER_ICON_ALIASES`` (for ``{% icon %}`` in templates). Another
theme keeps the keys and swaps the values.
"""

ACME_ICONS: dict[str, str] = {
    # entities
    "customer": "building-store",
    "address": "map-pin",
    "order": "receipt",
    "subscription": "repeat",
    "product": "package",
    "beans": "plant-2",
    "equipment": "tool",
    "category": "category",
    "lot": "package-import",
    "cupping": "coffee",
    "batch": "flame",
    "shipment": "truck-delivery",
    # sidebar sections
    "sales": "building-store",
    "catalog": "package",
    "roastery": "flame",
    # property groups
    "about": "info-circle",
    "pricing": "tags",
    "stock": "scale",
    "origin": "map-pin",
    # actions
    "packing-slip": "printer",
    "duplicate": "copy",
    "run-subscriptions": "player-play",
    "table-view": "table",
    "mark-default": "star",
    # workflow steps and shipment events
    "confirm": "check",
    "roasted": "coffee",
    "shipped": "package",
    "delivered": "circle-check",
    "cancelled": "circle-x",
    "picked-up": "package",
    "in-transit": "truck-delivery",
}
