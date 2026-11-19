"""Shared rendering helpers. Tasks 3 to 6 import these; keep the shapes stable."""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.utils import render_crispy_form
from django import forms
from django.template import engines

PACK = "crispy_tabler"


class RatingForm(forms.Form):
    rating = forms.IntegerField(widget=forms.NumberInput(attrs={"type": "range"}))
    accent_color = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))


def render_field(field, name="field", tag=None, **context):
    """Render one form field through the pack's field.html."""
    form = type("OneFieldForm", (forms.Form,), {name: field})()
    template = engines["django"].from_string("{% include 'crispy_tabler/field.html' %}")
    ctx = {"field": form[name], "form_show_labels": True, **context}
    if tag:
        ctx["tag"] = tag
    return template.render(ctx)


def _render_with_helper(helper, form):
    return render_crispy_form(form, helper, context={})


def render_layout(*layout_objects, form=None, helper=None):
    """Render a form through a FormHelper whose layout is the given objects."""
    from tests.crispy_tabler.forms import CoverageForm

    if helper is None:  # FormHelper defines __len__, so an empty one is falsy
        helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(*layout_objects)
    return _render_with_helper(helper, form or CoverageForm())


def render_horizontal(*layout_objects, form=None):
    helper = FormHelper()
    helper.form_class = "form-horizontal"
    helper.label_class = "col-sm-3"
    helper.field_class = "col-sm-9"
    return render_layout(*layout_objects, form=form, helper=helper)


def bound_with_error(name, form_class=RatingForm):
    """Render the named field of a bound, invalid RatingForm-like form."""
    form = form_class(data={"rating": "not a number", "accent_color": ""})
    form.is_valid()
    template = engines["django"].from_string("{% include 'crispy_tabler/field.html' %}")
    return template.render({"field": form[name], "form_show_labels": True})
