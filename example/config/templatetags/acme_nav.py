"""``{% load acme_nav %}``: the Acme navigation, defined once for the sidebar and the top bar (registered in TEMPLATES).

``django_tabler/includes/nav_menu.html`` renders it as section headings in the sidebar and as one dropdown per
section in the top bar, where fourteen links side by side do not fit.
"""

from dataclasses import dataclass, field

from django import template
from django.urls import reverse

register = template.Library()


@dataclass(frozen=True)
class Entry:
    title: str
    url_name: str
    icon: str
    # url names (without namespace) that mark this entry active: exact names or prefixes ending in "-"
    matches: tuple[str, ...]
    # any one of these permissions shows the entry; empty: every signed-in user
    perms: tuple[str, ...] = ()


@dataclass(frozen=True)
class Section:
    title: str
    icon: str
    entries: tuple[Entry, ...] = field(default_factory=tuple)


DASHBOARD = Entry("Dashboard", "dashboard:index", "dashboard", ("index",))

# Account managers hold only `add_customer` globally: their view rights are Guardian object grants, which a
# permission check without an object cannot see, so Customers opens for add or view.
MENU = (
    Section("Sales", "building-store", (
        Entry("Customers", "customer-list", "building-store", ("customer-", "address-"),
              ("sales.view_customer", "sales.add_customer")),
        Entry("Orders", "orders-list", "receipt", ("order-", "orders-"), ("sales.view_order",)),
        Entry("Subscriptions", "subscriptions-list", "repeat", ("subscription-", "subscriptions-"),
              ("sales.view_customersubscription",)),
    )),
    Section("Catalog", "package", (
        Entry("Products", "product-list", "package", ("product-",), ("catalog.view_product",)),
        Entry("Categories", "category-list", "category", ("category-",), ("catalog.view_category",)),
    )),
    Section("Roastery", "flame", (
        Entry("Green lots", "lot-list", "package-import", ("lot-", "cupping-"), ("roastery.view_greenlot",)),
        Entry("Roast batches", "batch-list", "flame", ("batch-",), ("roastery.view_roastbatch",)),
        # the shipment list checks `sales.view_order` and scopes the rows to the user's customers
        Entry("Shipments", "shipment-list", "truck-delivery", ("shipment-",), ("sales.view_order",)),
    )),
    Section("Developer", "code", (
        Entry("Form showcase", "showcaseitem-list", "layout-grid", ("showcaseitem-",), ("showcase.view_showcaseitem",)),
        Entry("How this is themed", "theming", "palette", ("theming",)),
    )),
    Section("Users", "users", (
        Entry("Users", "dashboard:users", "users", ("users", "user_create"), ("auth.view_user",)),
    )),
)


def _is_active(entry: Entry, url_name: str | None) -> bool:
    if not url_name:
        return False
    return any(url_name.startswith(m) if m.endswith("-") else url_name == m for m in entry.matches)


def _link(entry: Entry, url_name: str | None, current: str | None) -> dict:
    url = reverse(entry.url_name)
    return {"title": entry.title, "url": url, "icon": entry.icon, "active": _is_active(entry, url_name),
            "current": current == url}


@register.simple_tag(takes_context=True)
def acme_menu(context) -> dict:
    """The entries the user may open: ``{"dashboard": link, "sections": [{"title", "icon", "active", "links"}]}``."""
    request = context["request"]
    user = request.user
    match = request.resolver_match
    url_name = match.url_name if match else None
    current = request.path
    sections = []
    for section in MENU:
        links = [_link(e, url_name, current) for e in section.entries if not e.perms or any(user.has_perm(p) for p in e.perms)]
        if links:
            sections.append({"title": section.title, "icon": section.icon, "links": links,
                             "active": any(link["active"] for link in links)})
    return {"dashboard": _link(DASHBOARD, url_name, current), "sections": sections}
