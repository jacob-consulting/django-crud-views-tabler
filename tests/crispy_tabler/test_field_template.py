from django import forms

from tests.crispy_tabler.helpers import bound_with_error, render_field


def test_range_input_gets_form_range_not_form_control():
    html = render_field(forms.IntegerField(widget=forms.NumberInput(attrs={"type": "range"})))
    assert "form-range" in html and "form-control" not in html


def test_color_input_gets_form_control_color():
    html = render_field(forms.CharField(widget=forms.TextInput(attrs={"type": "color"})))
    assert "form-control-color" in html and 'class="textinput form-control"' not in html


def test_range_and_color_carry_is_invalid_when_the_field_has_errors():
    for html in (bound_with_error("rating"), bound_with_error("accent_color")):
        assert "is-invalid" in html
    assert "form-range is-invalid" in bound_with_error("rating")
    assert "form-control-color is-invalid" in bound_with_error("accent_color")


def test_a_radio_group_legend_is_a_plain_form_label():
    html = render_field(forms.ChoiceField(choices=[("a", "A")], widget=forms.RadioSelect))
    assert "fs-6" not in html and "form-label" in html


def test_a_hidden_field_renders_bare():
    html = render_field(forms.CharField(widget=forms.HiddenInput()))
    assert "<label" not in html and "mb-3" not in html


def test_a_file_field_renders_its_help_text_once():
    html = render_field(forms.FileField(help_text="Max 2 MB"))
    assert html.count("Max 2 MB") == 1


def test_a_checkbox_in_a_table_cell_has_no_wrapper_div():
    html = render_field(forms.BooleanField(), tag="td")
    assert html.count("<div") == 0


def test_inline_radio_and_checkbox_group_legends_are_plain_form_labels():
    from crispy_forms.bootstrap import InlineCheckboxes, InlineRadios

    from tests.crispy_tabler.helpers import render_layout

    for obj in (InlineRadios("radio"), InlineCheckboxes("checkbox_group")):
        html = render_layout(obj)
        assert "<legend" in html
        assert "fs-6" not in html and "form-label" in html
