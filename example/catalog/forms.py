"""Forms for the catalog: one model form per product kind, and the type picker's crispy wrapper."""

from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.layout import Row
from crud_views.lib.crispy import Column2, Column3, Column4, Column6, Column12, CrispyForm, CrispyModelForm
from crud_views_polymorphic.lib import PolymorphicContentTypeForm
from django import forms

from .models import Beans, Category, Equipment, Subscription

COMMON = ["name", "slug", "sku", "price", "stock", "is_active", "category", "description"]


class ProductContentTypeForm(CrispyForm, PolymorphicContentTypeForm):
    """Step one of "New product": pick the kind."""

    submit_label = "Continue"

    def get_layout_fields(self):
        return Row(Column4("polymorphic_ctype_id"))


class ProductFormBase(CrispyModelForm):
    """Shared layout: the name row, then commerce and description. Each kind inserts its own row after the name row."""

    submit_label = "Save"

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column3("slug"), Column3("sku")),
            Row(Column3("price"), Column3("stock"), Column3("category"), Column3("is_active")),
            Row(Column12("description")),
        ]


class BeansForm(ProductFormBase):
    class Meta:
        model = Beans
        fields = [*COMMON, "origin", "green_lot", "process", "altitude_m", "roast_level", "flavor_notes"]
        widgets = {"flavor_notes": forms.CheckboxSelectMultiple}

    def get_layout_fields(self):
        base = super().get_layout_fields()
        return [
            base[0],
            Row(Column4("origin"), Column4("green_lot"), Column2("process"), Column2("roast_level")),
            Row(Column2("altitude_m")),
            Row(Column12(InlineCheckboxes("flavor_notes"))),
            *base[1:],
        ]


class EquipmentForm(ProductFormBase):
    class Meta:
        model = Equipment
        fields = [*COMMON, "brand", "warranty_months", "weight_kg"]

    def get_layout_fields(self):
        base = super().get_layout_fields()
        return [base[0], Row(Column4("brand"), Column4("warranty_months"), Column4("weight_kg")), *base[1:]]


class SubscriptionForm(ProductFormBase):
    class Meta:
        model = Subscription
        fields = [*COMMON, "interval", "bags_per_delivery", "bag_size"]

    def get_layout_fields(self):
        base = super().get_layout_fields()
        return [base[0], Row(Column4("interval"), Column4("bags_per_delivery"), Column4("bag_size")), *base[1:]]


POLYMORPHIC_FORMS = {Beans: BeansForm, Equipment: EquipmentForm, Subscription: SubscriptionForm}


class CategoryForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Category
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))
