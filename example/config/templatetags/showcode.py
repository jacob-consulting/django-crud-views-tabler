"""``{% load showcode %}``: the "Show code" panel of the example's crud_views pages (registered in TEMPLATES).

The page only gets the collapsed shell; the sources are fetched from ``/_code/<app_label>/`` when it opens.
"""

from django import template
from django.urls import reverse

from config.showcode import code_app_label, own_module_label

register = template.Library()


@register.simple_tag(takes_context=True)
def code_panel_url(context) -> str:
    """The fragment URL of the current view's code panel, or "" when the view has none. Reads no files."""
    view = context.get("view")
    label = code_app_label(view) if view is not None else None
    return reverse("code-panel", kwargs={"app_label": label}) if label else ""


@register.inclusion_tag("project/code_panel_shell.html", takes_context=True)
def code_panel(context):
    view = context.get("view")
    return {"code_url": code_panel_url(context), "active_file": own_module_label(view) if view is not None else ""}
