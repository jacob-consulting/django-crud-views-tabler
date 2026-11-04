"""Forms for customers and addresses.

The wholesale-only fields sit in a conditional group. Upstream's toggles are boolean, and ``Customer.kind`` is a
choice, so the form carries a transient ``is_wholesale`` checkbox that decides the group and is then stored as
``kind`` (see the roastery findings).
"""

from crispy_forms.layout import Row
from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupModelForm, ToggleGroup, UIFieldToggle
from crud_views.lib.crispy import Column2, Column3, Column4, Column6, Column12, CrispyModelForm
from django import forms

from .models import Address, Customer

WHOLESALE_FIELDS = ["company", "vat_id", "price_tier", "payment_terms"]


class CustomerForm(ConditionalGroupModelForm):
    submit_label = "Save"
    is_wholesale = forms.BooleanField(required=False, label="Wholesale customer")

    cv_conditional_groups = [
        ConditionalGroup(
            toggle=UIFieldToggle("is_wholesale"),
            fields=WHOLESALE_FIELDS,
            required=["company", "price_tier", "payment_terms"],
            empty_values={"company": "", "vat_id": "", "price_tier": None, "payment_terms": None},
        )
    ]

    class Meta:
        model = Customer
        fields = [
            "name", "contact_name", "email", "phone", "city", "country", "owner", *WHOLESALE_FIELDS, "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # a model-declared form field would be redeclared by the mixin; keep the declared one, seed it from the row
        self.fields["is_wholesale"].initial = self.instance.is_wholesale
        self.fields["owner"].empty_label = "Unassigned"
        self.fields["country"].help_text = "ISO country code, e.g. DE."

    def clean(self):
        cleaned = super().clean()
        self.instance.kind = Customer.Kind.WHOLESALE if cleaned.get("is_wholesale") else Customer.Kind.CONSUMER
        return cleaned

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column6("contact_name")),
            Row(Column4("email"), Column3("phone"), Column3("city"), Column2("country")),
            Row(Column4("owner")),
            Row(Column12("is_wholesale")),
            ToggleGroup(
                "is_wholesale",
                Row(Column6("company"), Column6("vat_id")),
                Row(Column4("price_tier"), Column4("payment_terms")),
                legend="Wholesale terms",
            ),
            Row(Column12("notes")),
        ]


class AddressForm(CrispyModelForm):
    submit_label = "Save"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["country"].help_text = "ISO country code, e.g. DE."

    class Meta:
        model = Address
        fields = ["label", "street", "zip_code", "city", "country", "is_default"]

    def get_layout_fields(self):
        return [
            Row(Column4("label")),
            Row(Column12("street")),
            Row(Column3("zip_code"), Column6("city"), Column3("country")),
            Row(Column12("is_default")),
        ]
