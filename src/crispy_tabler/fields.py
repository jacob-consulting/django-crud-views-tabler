"""Form fields that bind the widgets in widgets.py, and nothing more."""

from django import forms

from .widgets import ColorInput, PlaintextInput, RangeInput


class PlaintextField(forms.CharField):
    """A read-only value. Disabled, so a posted value is ignored for the initial."""

    widget = PlaintextInput

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("disabled", True)
        super().__init__(**kwargs)


class RangeField(forms.IntegerField):
    widget = RangeInput


class ColorField(forms.CharField):
    widget = ColorInput
