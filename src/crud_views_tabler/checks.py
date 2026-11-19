from crud_views.lib.icons import _get_renderers, _icon_str, get_icons
from django.core.checks import CheckMessage, Tags, Warning, register

from crud_views_tabler.icons import render
from django_tabler.icons import ICONS


@register(Tags.templates)
def check_tabler_icons(app_configs=None, **kwargs) -> list[CheckMessage]:
    """Warn when a ``tabler:`` icon value has no SVG path in ``django_tabler.icons.ICONS``."""
    messages: list[CheckMessage] = []
    if _get_renderers().get("tabler") is not render:
        return messages  # the project remapped the prefix to another renderer
    for key, value in get_icons().items():
        stripped = _icon_str(value)
        if stripped is None or not stripped.startswith("tabler:"):
            continue
        name = stripped.split(":", 1)[1]
        if name not in ICONS:
            messages.append(
                Warning(
                    f"Icon {key!r} = {value!r}: crud_views_tabler has no SVG for Tabler icon {name!r}.",
                    hint="Add its <path d> values to django_tabler.icons.ICONS or use another library prefix.",
                    id="crud_views_tabler.W001",
                )
            )
    return messages
