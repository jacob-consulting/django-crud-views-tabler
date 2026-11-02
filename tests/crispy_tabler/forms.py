"""Shared forms for the rendering tests.

CoverageForm carries one field per render path of the pack. Later tasks reuse
it, so keep the field names and order stable.
"""

from django import forms


class CoverageForm(forms.Form):
    char = forms.CharField(help_text="A char field")
    textarea = forms.CharField(widget=forms.Textarea)
    select = forms.ChoiceField(choices=[("a", "A"), ("b", "B")])
    multi_select = forms.MultipleChoiceField(choices=[("a", "A"), ("b", "B")])
    checkbox = forms.BooleanField(required=False)
    radio = forms.ChoiceField(
        choices=[("a", "A"), ("b", "B")], widget=forms.RadioSelect
    )
    checkbox_group = forms.MultipleChoiceField(
        choices=[("a", "A"), ("b", "B")], widget=forms.CheckboxSelectMultiple
    )
    file = forms.FileField()
    email = forms.EmailField()
    url = forms.URLField()
    number = forms.IntegerField()
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
