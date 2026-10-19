"""Tabler outline icons (https://tabler.io/icons) rendered as inline SVG.

django-crud-views names its icons with Font Awesome classes (``cv_icon_action = "fa-regular fa-eye"``).
``render_icon`` accepts either a Tabler icon name from ``ICONS`` or such a Font Awesome class string, which
it maps through ``FONT_AWESOME``. Anything it does not know is rendered as the original ``<i class>`` so a
project that also loads Font Awesome keeps working.
"""

from django.utils.html import format_html, format_html_join

ICONS = {
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
    "check": ["M5 12l5 5l10 -10"],
    "chevron-left": ["M15 6l-6 6l6 6"],
    "chevron-right": ["M9 6l6 6l-6 6"],
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
    "filter": [
        "M4 4h16v2.172a2 2 0 0 1 -.586 1.414l-4.414 4.414v7l-6 2v-8.5l-4.48 -4.928a2 2 0 0 1 -.52 -1.345v-2.227"
    ],
    "home": [
        "M5 12l-2 0l9 -9l9 9l-2 0",
        "M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-7",
        "M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v6",
    ],
    "info-circle": ["M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0", "M12 9h.01", "M11 12h1v4h1"],
    "layout-grid": [
        "M4 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M4 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
    ],
    "list": ["M9 6l11 0", "M9 12l11 0", "M9 18l11 0", "M5 6l0 .01", "M5 12l0 .01", "M5 18l0 .01"],
    "moon": ["M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454l0 .008"],
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
    "square-plus": [
        "M9 12h6",
        "M12 9v6",
        "M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14",
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

# Font Awesome icon name (without style prefix) -> Tabler icon name, for the defaults django-crud-views ships.
FONT_AWESOME = {
    "fa-eye": "eye",
    "fa-pen-to-square": "pencil",
    "fa-trash-can": "trash",
    "fa-square-plus": "square-plus",
    "fa-rectangle-list": "list",
    "fa-circle-up": "arrow-up",
    "fa-circle-down": "arrow-down",
    "fa-gear": "settings",
    "fa-filter": "filter",
    "fa-ellipsis": "dots",
    "fa-house": "home",
    "fa-arrow-left": "arrow-left",
    "fa-user": "user",
    "fa-users": "users",
}


def resolve(value):
    """Tabler icon name for ``value`` (a Tabler name or a Font Awesome class string), or None."""
    if not value:
        return None
    if value in ICONS:
        return value
    for css_class in value.split():
        if css_class in FONT_AWESOME:
            return FONT_AWESOME[css_class]
    return None


def render_icon(value, css_class=""):
    """Inline SVG for a known icon; the original ``<i class>`` otherwise; empty for no icon."""
    if not value:
        return ""
    name = resolve(value)
    if name is None:
        return format_html('<i class="{}" aria-hidden="true"></i>', f"{value} {css_class}".strip())
    paths = format_html_join("", '<path d="{}" />', ((d,) for d in ICONS[name]))
    return format_html(
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false" class="{}">{}</svg>',
        f"icon {css_class}".strip(),
        paths,
    )
