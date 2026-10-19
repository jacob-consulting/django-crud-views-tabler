from django import template

from crud_views_tabler.icons import render_icon

register = template.Library()


@register.simple_tag
def cvt_icon(value, css_class=""):
    """``{% cvt_icon cv_icon_action "icon-sm" %}`` - a Tabler SVG for a Tabler name or Font Awesome class."""
    return render_icon(value, css_class)
