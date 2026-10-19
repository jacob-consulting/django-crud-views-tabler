from django import template
from django.utils.html import format_html, format_html_join

register = template.Library()

# Outline icons from Tabler Icons (https://tabler.io/icons), one entry per path.
ICONS = {
    "dashboard": [
        "M5 4h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1",
        "M5 16h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1",
        "M15 12h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1",
        "M15 4h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1",
    ],
    "users": [
        "M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0",
        "M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2",
        "M16 3.13a4 4 0 0 1 0 7.75",
        "M21 21v-2a4 4 0 0 0 -3 -3.85",
    ],
    "moon": ["M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454l0 .008"],
    "sun": [
        "M8 12a4 4 0 1 0 8 0a4 4 0 1 0 -8 0",
        "M3 12h1m8 -9v1m8 8h1m-9 8v1m-6.4 -15.4l.7 .7m12.1 -.7l-.7 .7m0 11.4l.7 .7m-12.1 -.7l-.7 .7",
    ],
    "plus": ["M12 5l0 14", "M5 12l14 0"],
    "search": ["M3 10a7 7 0 1 0 14 0a7 7 0 1 0 -14 0", "M21 21l-6 -6"],
    "eye": [
        "M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0",
        "M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6",
    ],
    "trending-up": ["M3 17l6 -6l4 4l8 -8", "M14 7l7 0l0 7"],
    "trending-down": ["M3 7l6 6l4 -4l8 8", "M21 10l0 7l-7 0"],
    "check": ["M5 12l5 5l10 -10"],
    "alert-circle": ["M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0", "M12 8v4", "M12 16h.01"],
    "info-circle": ["M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0", "M12 9h.01", "M11 12h1v4h1"],
}

AVATAR_COLORS = ["blue", "green", "purple", "azure", "orange", "pink", "teal", "red"]


@register.simple_tag
def icon(name, css_class=""):
    """Render a Tabler outline icon as inline SVG: {% icon "users" "icon-sm" %}."""
    paths = format_html_join("", '<path d="{}" />', ((d,) for d in ICONS[name]))
    return format_html(
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false" class="{}">{}</svg>',
        f"icon {css_class}".strip(),
        paths,
    )


@register.filter
def initials(user):
    """Two-letter initials from the user's name, falling back to the username."""
    name = user.get_full_name().split()
    if len(name) >= 2:
        return (name[0][0] + name[-1][0]).upper()
    return user.get_username()[:2].upper()


@register.filter
def avatar_color(user):
    """A stable avatar colour per user."""
    return AVATAR_COLORS[(user.pk or 0) % len(AVATAR_COLORS)]


@register.filter
def form_control(field, css_class="form-control"):
    """Render a bound field's widget with a Tabler class, marked invalid when it has errors."""
    attrs = {"class": css_class}
    if field.errors:
        attrs["class"] += " is-invalid"
        attrs["aria-invalid"] = "true"
        attrs["aria-describedby"] = f"{field.auto_id}-errors"
    elif field.help_text:
        attrs["aria-describedby"] = f"{field.auto_id}-help"
    return field.as_widget(attrs=attrs)
