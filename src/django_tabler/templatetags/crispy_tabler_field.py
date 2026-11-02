from django import template

register = template.Library()


def _input_type(field):
    # The type attribute wins: forms.NumberInput(attrs={"type": "range"}) has
    # input_type "number", but renders type="range". Fall back to input_type
    # for widgets that declare it (RangeInput, ColorInput).
    widget = field.field.widget
    return widget.attrs.get("type") or getattr(widget, "input_type", None)


@register.filter
def is_range(field):
    return _input_type(field) == "range"


@register.filter
def is_color(field):
    return _input_type(field) == "color"
