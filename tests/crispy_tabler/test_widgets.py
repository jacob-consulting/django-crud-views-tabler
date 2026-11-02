import re

from django import forms

from crispy_tabler.fields import ColorField, PlaintextField, RangeField
from crispy_tabler.templatetags.crispy_tabler_field import is_color, is_range
from crispy_tabler.widgets import ColorInput, PlaintextInput, RangeInput
from tests.crispy_tabler.helpers import render_field


def field_with(widget):
    form = type("F", (forms.Form,), {"f": forms.CharField(widget=widget)})()
    return form["f"]


def test_range_and_color_widgets_are_detected_by_the_filters():
    # These widgets carry no "type" attr, so detection must use input_type.
    assert "type" not in RangeInput(min=1, max=5).attrs
    assert "type" not in ColorInput().attrs
    assert is_range(field_with(RangeInput(min=1, max=5)))
    assert is_color(field_with(ColorInput()))


def test_plaintext_widget_renders_the_value_not_an_input():
    html = render_field(forms.CharField(widget=PlaintextInput(), initial="SKU-1"))
    assert "form-control-plaintext" in html and "<input" not in html
    assert "SKU-1" in html


def test_plaintext_widget_escapes_its_value():
    html = render_field(forms.CharField(widget=PlaintextInput(), initial="<b>x</b>"))
    assert "<b>x</b>" not in html and "&lt;b&gt;" in html


def test_range_widget_carries_its_bounds():
    html = render_field(forms.IntegerField(widget=RangeInput(min=1, max=5)))
    assert 'min="1"' in html and 'max="5"' in html and "form-range" in html


def test_color_widget_renders_a_color_swatch():
    html = render_field(forms.CharField(widget=ColorInput()))
    assert 'type="color"' in html and "form-control-color" in html


def test_fields_bind_their_widgets():
    assert isinstance(PlaintextField().widget, PlaintextInput)
    assert isinstance(RangeField().widget, RangeInput)
    assert isinstance(ColorField().widget, ColorInput)


def test_plaintext_widget_renders_a_clean_div():
    html = render_field(forms.CharField(widget=PlaintextInput(), initial="SKU-1"))
    tag = re.search(r"<div class=\"form-control-plaintext[^>]*>SKU-1</div>", html).group(0)
    assert tag.count("class=") == 1
    for bad in ("form-control ", "plaintextinput", "required", "disabled"):
        assert bad not in tag


def test_plaintext_widget_keeps_a_callers_class():
    widget = PlaintextInput(attrs={"class": "fw-bold"})
    html = render_field(forms.CharField(widget=widget, initial="x"))
    assert 'class="form-control-plaintext fw-bold"' in html


def test_plaintext_field_renders_without_disabled_on_the_div():
    html = render_field(PlaintextField(initial="x"))
    assert "disabled" not in html and ">x</div>" in html


def test_range_field_bounds_are_validated_and_rendered():
    field = RangeField(min_value=1, max_value=5)
    html = render_field(field)
    assert 'min="1"' in html and 'max="5"' in html
    try:
        field.clean("99")
    except forms.ValidationError:
        pass
    else:
        raise AssertionError("99 should be rejected")
