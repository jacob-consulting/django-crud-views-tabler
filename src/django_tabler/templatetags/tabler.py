import json
import re

from django import template
from django.conf import settings
from django.contrib.messages import constants
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django_tabler.icons import svg

register = template.Library()

MESSAGE_ALERTS = {
    constants.DEBUG: {"css": "alert alert-secondary", "icon": "bug"},
    constants.INFO: {"css": "alert alert-info", "icon": "info-circle"},
    constants.SUCCESS: {"css": "alert alert-success", "icon": "check"},
    constants.WARNING: {"css": "alert alert-warning", "icon": "alert-triangle"},
    constants.ERROR: {"css": "alert alert-danger", "icon": "alert-circle"},
}

AVATAR_COLORS = ["blue", "green", "purple", "azure", "orange", "pink", "teal", "red"]


@register.simple_tag
def icon(name, css_class=""):
    """Render a Tabler outline icon as inline SVG: {% icon "users" "icon-sm" %}.

    ``name`` is resolved through ``settings.TABLER_ICON_ALIASES`` first; unknown names pass through unchanged.
    """
    name = getattr(settings, "TABLER_ICON_ALIASES", {}).get(name, name)
    return svg(name, css_class)


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


@register.filter
def message_alert(message):
    """Alert class and icon for a Django message; a custom level renders as info."""
    return MESSAGE_ALERTS.get(getattr(message, "level", None), MESSAGE_ALERTS[constants.INFO])


# Tabler's layout settings (tabler-theme.js themeDefaults) that a project may preset, with Tabler's defaults.
TABLER_LAYOUT_DEFAULTS = {
    "layout": "default",
    "navbar-position": "horizontal",
    "navbar-style": "default",
    "navbar-theme": "default",
    "sidebar": "default",
}
_LAYOUT_VALUE = re.compile(r"^[a-z0-9-]{1,32}$")  # tabler-theme.js's VALUE_PATTERN


@register.simple_tag
def layout_defaults_attrs():
    """Attributes for <html> from the project's default layout (``django_tabler/includes/layout_defaults.html``).

    Each value that differs from Tabler's default becomes ``data-bs-<key>``, which tabler-theme.js treats as the
    server value: a choice the user stored in localStorage still wins. ``data-tabler-layout-defaults`` hands the
    defaults to layout-switch.js. Renders nothing for the package's empty default.
    """
    raw = render_to_string("django_tabler/includes/layout_defaults.html").strip()
    try:
        defaults = json.loads(raw or "{}")
    except json.JSONDecodeError as error:
        raise ValueError(f"django_tabler/includes/layout_defaults.html is not JSON: {error}") from None
    if not isinstance(defaults, dict):
        raise ValueError("django_tabler/includes/layout_defaults.html must hold a JSON object")
    for key, value in defaults.items():
        if key not in TABLER_LAYOUT_DEFAULTS or not isinstance(value, str) or not _LAYOUT_VALUE.match(value):
            raise ValueError(f"layout default {key!r}: {value!r} is not a Tabler layout setting")
    if not defaults:
        return ""
    attrs = [format_html(' data-bs-{}="{}"', k, v) for k, v in defaults.items() if v != TABLER_LAYOUT_DEFAULTS[k]]
    attrs.append(format_html(' data-tabler-layout-defaults="{}"', json.dumps(defaults)))
    return mark_safe("".join(attrs))
