from django.core.checks import CheckMessage, Tags, Warning, register

from crud_views.lib.icons import get_icons
from crud_views_tabler.icons import ICONS


@register(Tags.templates)
def check_tabler_icons(app_configs=None, **kwargs) -> list[CheckMessage]:
    """Warn when a ``tabler:`` icon value has no SVG path in ``crud_views_tabler.icons.ICONS``."""
    messages: list[CheckMessage] = []
    for key, value in get_icons().items():
        if not isinstance(value, str) or not value.startswith("tabler:"):
            continue
        name = value.split(":", 1)[1]
        if name not in ICONS:
            messages.append(
                Warning(
                    f"Icon {key!r} = {value!r}: crud_views_tabler has no SVG for Tabler icon {name!r}.",
                    hint="Add its <path d> values to crud_views_tabler.icons.ICONS or use another library prefix.",
                    id="crud_views_tabler.W001",
                )
            )
    return messages
