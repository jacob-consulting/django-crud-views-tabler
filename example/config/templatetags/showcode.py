"""``{% load showcode %}``: the "Show code" panel of the example's crud_views pages (registered in TEMPLATES)."""

from django import template
from django.utils.html import strip_tags

from config.showcode import collect_app_sources

register = template.Library()

THEME_PACKAGES = ("django_tabler", "crud_views_tabler")


def _sources(context):
    view = context.get("view")
    return collect_app_sources(view) if view is not None else []


def _short(label: str, app_label: str) -> str:
    """``sales/templates/sales/x.html`` -> ``sales/x.html``, ``sales/views/orders.py`` -> ``views/orders.py``."""
    short = label.removeprefix(f"{app_label}/")
    return short.removeprefix("templates/")


@register.inclusion_tag("project/code_panel.html", takes_context=True)
def code_panel(context):
    """A collapsed card with one pill per app file of the current view (``id="code-panel"``)."""
    sources = _sources(context)
    app_label = type(context.get("view")).__module__.split(".")[0] if sources else ""
    return {
        "files": [{"source": s, "short": _short(s.label, app_label)} for s in sources],
        "app_label": app_label,
        "total_lines": sum(s.lines for s in sources),
        "imports_theme": any(name in strip_tags(s.html) for s in sources for name in THEME_PACKAGES),
    }


@register.simple_tag(takes_context=True)
def has_code_panel(context) -> bool:
    return bool(_sources(context))
