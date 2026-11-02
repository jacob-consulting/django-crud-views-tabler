from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Fieldset, Submit

from crispy_tabler.layout import UneditableField

from tests.crispy_tabler.helpers import render_horizontal, render_layout


def test_uneditable_field_is_a_plaintext_control():
    html = render_layout(UneditableField("char"))
    assert "form-control-plaintext" in html and "uneditable-input" not in html


def test_uneditable_field_label_is_a_form_label():
    assert '<label class="form-label ' in render_layout(UneditableField("char"))


def test_form_actions_get_the_tabler_footer():
    html = render_layout(FormActions(Submit("save", "Save")))
    assert "form-footer" in html


def test_fieldset_gets_the_tabler_class_by_default():
    assert "form-fieldset" in render_layout(Fieldset("Internal", "char"))


def test_an_explicit_css_class_still_wins_on_fieldset():
    html = render_layout(Fieldset("Internal", "char", css_class="custom"))
    assert 'class="form-fieldset custom"' in html


def test_a_horizontal_form_keeps_its_label_columns():
    html = render_horizontal(UneditableField("char"))
    assert "col-form-label" in html


def test_uneditable_field_keeps_an_explicit_css_class():
    html = render_layout(UneditableField("char", css_class="extra"))
    assert "form-control-plaintext extra" in html and "uneditable-input" not in html
