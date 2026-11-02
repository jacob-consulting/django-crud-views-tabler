from django import template

from crud_views_tabler.icons import svg

register = template.Library()

AVATAR_COLORS = ["blue", "green", "purple", "azure", "orange", "pink", "teal", "red"]


@register.simple_tag
def icon(name, css_class=""):
    """Render a Tabler outline icon as inline SVG: {% icon "users" "icon-sm" %}."""
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
