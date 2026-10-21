"""Tabler outline icons (https://tabler.io/icons) rendered as inline SVG.

The icons plug into django-crud-views' icon registry as the ``tabler`` library (``tabler:eye``, see ``render``).
``TABLER_ICONS`` maps the package's semantic icon names to Tabler icons; a project overrides single keys with
``CRUD_VIEWS_ICONS``. ``svg`` renders a Tabler icon directly, e.g. for the dashboard's ``{% icon %}`` tag.
"""

from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString

ICONS: dict[str, list[str]] = {
    "alert-circle": ["M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0", "M12 8v4", "M12 16h.01"],
    "arrow-down": ["M12 5l0 14", "M18 13l-6 6", "M6 13l6 6"],
    "arrow-left": ["M5 12l14 0", "M5 12l6 6", "M5 12l6 -6"],
    "arrow-up": ["M12 5l0 14", "M18 11l-6 -6", "M6 11l6 -6"],
    "building-store": [
        "M3 21l18 0",
        "M3 7v1a3 3 0 0 0 6 0v-1m0 1a3 3 0 0 0 6 0v-1m0 1a3 3 0 0 0 6 0v-1h-18l2 -4h14l2 4",
        "M5 21l0 -10.15",
        "M19 21l0 -10.15",
        "M9 21v-4a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v4",
    ],
    "caret-down": ["M6 10l6 6l6 -6h-12"],
    "caret-up": ["M18 14l-6 -6l-6 6h12"],
    "check": ["M5 12l5 5l10 -10"],
    "chevron-left": ["M15 6l-6 6l6 6"],
    "chevron-right": ["M9 6l6 6l-6 6"],
    "chevrons-down": ["M7 7l5 5l5 -5", "M7 13l5 5l5 -5"],
    "chevrons-right": ["M7 7l5 5l-5 5", "M13 7l5 5l-5 5"],
    "chevrons-up": ["M7 11l5 -5l5 5", "M7 17l5 -5l5 5"],
    "circle-check": ["M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0", "M9 12l2 2l4 -4"],
    "circle-x": ["M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0", "M10 10l4 4m0 -4l-4 4"],
    "corner-left-up": ["M18 18h-6a3 3 0 0 1 -3 -3v-10l-4 4m8 0l-4 -4"],
    "dashboard": [
        "M5 4h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1",
        "M5 16h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1",
        "M15 12h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1",
        "M15 4h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1",
    ],
    "dots": [
        "M4 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
        "M11 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
        "M18 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
    ],
    "eye": [
        "M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0",
        "M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6",
    ],
    "file-text": [
        "M14 3v4a1 1 0 0 0 1 1h4",
        "M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2",
        "M9 9l1 0",
        "M9 13l6 0",
        "M9 17l6 0",
    ],
    "filter": [
        "M4 4h16v2.172a2 2 0 0 1 -.586 1.414l-4.414 4.414v7l-6 2v-8.5l-4.48 -4.928a2 2 0 0 1 -.52 -1.345v-2.227"
    ],
    "filter-x": [
        "M13.758 19.414l-4.758 1.586v-8.5l-4.48 -4.928a2 2 0 0 1 -.52 -1.345v-2.227h16v2.172a2 2 0 0 1 -.586 1.414l-4.414 4.414v1.5",
        "M22 22l-5 -5",
        "M17 22l5 -5",
    ],
    "hierarchy": [
        "M10 5a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M3 19a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M17 19a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M6.5 17.5l5.5 -4.5l5.5 4.5",
        "M12 7l0 6",
    ],
    "home": [
        "M5 12l-2 0l9 -9l9 9l-2 0",
        "M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-7",
        "M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v6",
    ],
    "info-circle": ["M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0", "M12 9h.01", "M11 12h1v4h1"],
    "language": [
        "M9 6.371c0 4.418 -2.239 6.629 -5 6.629",
        "M4 6.371h7",
        "M5 9c0 2.144 2.252 3.908 6 4",
        "M12 20l4 -9l4 9",
        "M19.1 18h-6.2",
        "M6.694 3l.793 .582",
    ],
    "layout-grid": [
        "M4 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M4 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
    ],
    "list": ["M9 6l11 0", "M9 12l11 0", "M9 18l11 0", "M5 6l0 .01", "M5 12l0 .01", "M5 18l0 .01"],
    "mood-empty": ["M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0", "M9 10l.01 0", "M15 10l.01 0", "M9 15l6 0"],
    "moon": ["M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454l0 .008"],
    "package": [
        "M12 3l8 4.5l0 9l-8 4.5l-8 -4.5l0 -9l8 -4.5",
        "M12 12l8 -4.5",
        "M12 12l0 9",
        "M12 12l-8 -4.5",
    ],
    "pencil": ["M4 20h4l10.5 -10.5a2.828 2.828 0 1 0 -4 -4l-10.5 10.5v4", "M13.5 6.5l4 4"],
    "plus": ["M12 5l0 14", "M5 12l14 0"],
    "search": ["M3 10a7 7 0 1 0 14 0a7 7 0 1 0 -14 0", "M21 21l-6 -6"],
    "settings": [
        "M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37"
        "a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826"
        " 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573"
        " -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0"
        " -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065",
        "M9 12a3 3 0 1 0 6 0a3 3 0 0 0 -6 0",
    ],
    "sort-ascending": ["M4 6l7 0", "M4 12l7 0", "M4 18l9 0", "M15 9l3 -3l3 3", "M18 6l0 12"],
    "sort-descending": ["M4 6l9 0", "M4 12l7 0", "M4 18l7 0", "M15 15l3 3l3 -3", "M18 6l0 12"],
    "square-plus": [
        "M9 12h6",
        "M12 9v6",
        "M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14",
    ],
    "square-x": [
        "M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14",
        "M9 9l6 6m0 -6l-6 6",
    ],
    "sun": [
        "M8 12a4 4 0 1 0 8 0a4 4 0 1 0 -8 0",
        "M3 12h1m8 -9v1m8 8h1m-9 8v1m-6.4 -15.4l.7 .7m12.1 -.7l-.7 .7m0 11.4l.7 .7m-12.1 -.7l-.7 .7",
    ],
    "trash": [
        "M4 7l16 0",
        "M10 11l0 6",
        "M14 11l0 6",
        "M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12",
        "M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3",
    ],
    "trending-down": ["M3 7l6 6l4 -4l8 8", "M21 10l0 7l-7 0"],
    "trending-up": ["M3 17l6 -6l4 4l8 -8", "M14 7l7 0l0 7"],
    "user": ["M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0", "M6 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2"],
    "users": [
        "M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0",
        "M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2",
        "M16 3.13a4 4 0 0 1 0 7.75",
        "M21 21v-2a4 4 0 0 0 -3 -3.85",
    ],
}

# django-crud-views semantic icon name -> Tabler icon (registered from apps.py; CRUD_VIEWS_ICONS overrides per key).
TABLER_ICONS: dict[str, str] = {
    "list": "tabler:list",
    "card": "tabler:layout-grid",
    "detail": "tabler:eye",
    "create": "tabler:square-plus",
    "update": "tabler:pencil",
    "delete": "tabler:trash",
    "order-up": "tabler:arrow-up",
    "order-down": "tabler:arrow-down",
    "manage": "tabler:settings",
    "workflow": "tabler:hierarchy",
    "actions-menu": "tabler:dots",
    "filter": "tabler:filter",
    "filter-close": "tabler:filter-x",
    "language": "tabler:language",
    "sort-asc": "tabler:sort-ascending",
    "sort-desc": "tabler:sort-descending",
    "table-sort-asc": "tabler:chevrons-up",
    "table-sort-desc": "tabler:chevrons-down",
    "formset-up": "tabler:caret-up",
    "formset-down": "tabler:caret-down",
    "formset-add": "tabler:plus",
    "formset-delete": "tabler:square-x",
    "field-marker": "tabler:chevrons-right",
    "boolean-true": "tabler:circle-check",
    "boolean-false": "tabler:circle-x",
    "property-detail": "tabler:info-circle",
    "text-icon": "tabler:file-text",
}


def svg(name: str | None, css: str = "") -> SafeString:
    """Inline SVG for a Tabler icon name; empty for no name or one not in ``ICONS``."""
    if not name or name not in ICONS:
        return SafeString("")
    paths = format_html_join("", '<path d="{}" />', ((d,) for d in ICONS[name]))
    return format_html(
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false" class="{}">{}</svg>',
        f"icon {css}".strip(),
        paths,
    )


def render(name: str, *, css: str, config: dict) -> SafeString:
    """Renderer of the ``tabler`` icon library in django-crud-views' icon registry."""
    return svg(name, css)
