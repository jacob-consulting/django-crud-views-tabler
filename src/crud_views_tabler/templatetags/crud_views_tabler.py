"""Theme tags for crud_views_tabler/page.html."""

from django import template
from django.utils.html import strip_tags

register = template.Library()


def _text(value) -> str:
    return " ".join(strip_tags(str(value)).split())


@register.simple_tag(takes_context=True)
def cv_tabler_heading_repeats_tab(context) -> bool:
    """True when a ViewSet Navigation bar is shown and the view's heading says the same as its active tab.

    Reads the documented ``cv_navbar`` mapping (``items``, ``active``, ``label``) and the view's ``cv_header``.
    Exact text after stripping tags and collapsing whitespace: a near miss keeps the heading.
    """
    navbar, view = context.get("cv_navbar"), context.get("view")
    if not navbar or view is None:
        return False
    active = [item for item in navbar["items"] if item["active"]]
    return bool(active) and _text(view.cv_header) == _text(active[0]["label"])
