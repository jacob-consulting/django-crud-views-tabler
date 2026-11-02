"""CRUD views for ``Product``.

``ProductForm`` is the reason this app exists: its layout uses one crispy layout object
per render path, so a single create page shows every branch of the crispy template pack
side by side. Keep that coverage when editing — the table in
``docs/crispy_tabler_coverage.md`` says which field covers which template.
"""

import django_filters
import django_tables2 as tables
from crispy_forms.bootstrap import AppendedText, InlineCheckboxes, InlineRadios, PrependedText
from crispy_forms.layout import Fieldset, Layout, Row
from django_tabler.crispy.layout import FloatingField, Switch, UneditableField
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.crispy import Column3, Column4, Column6, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.table.columns import NaturalTimeColumn
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ViewSet
from django import forms

from .models import Category, Product, Tag

cv_product = ViewSet(model=Product, name="product", icon_header="tabler:package")


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass


class ProductTable(Table):
    id = LinkDetailColumn(verbose_name="#")
    name = tables.Column()
    sku = tables.Column()
    category = tables.Column()
    price = tables.Column(attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}})
    stock = tables.TemplateColumn(
        template_code='<span class="badge bg-{{ record.stock_badge }}-lt">{{ record.stock }}</span>',
        attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}},
    )
    is_active = tables.BooleanColumn(verbose_name="Active")
    created_at = NaturalTimeColumn(verbose_name="Created")


class ProductFilter(django_filters.FilterSet):
    """Covers the widgets the model form cannot reach: a null-boolean select and a number pair."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple
    )
    is_featured = django_filters.BooleanFilter(label="Featured")
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte", label="Price from")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte", label="Price to")

    class Meta:
        model = Product
        fields = ["name", "category", "tags", "is_featured", "price_min", "price_max"]


class ProductFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(
        Row(Column4("name"), Column4("category"), Column4("is_featured")),
        Row(Column3("price_min"), Column3("price_max")),
        Row(Column12(InlineCheckboxes("tags"))),
    )


class ProductForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Product
        fields = [
            "name", "slug", "sku", "description",
            "category", "tags", "channels", "size", "shipping",
            "price", "warranty_months", "stock", "rating",
            "released_on", "published_at", "restock_at",
            "is_active", "is_featured",
            "accent_color", "contact_email", "website", "datasheet",
            "internal_notes",
        ]
        widgets = {
            "size": forms.RadioSelect,
            # InlineRadios only styles the markup; without RadioSelect the field keeps its
            # Select widget and crispy renders <input type="select">
            "shipping": forms.RadioSelect,
            "channels": forms.CheckboxSelectMultiple,
            "rating": forms.NumberInput(attrs={"type": "range", "min": 1, "max": 5, "step": 1}),
            "released_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "restock_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "accent_color": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # the warehouse owns the SKU: shown, never posted (UneditableField renders it disabled)
        self.fields["sku"].disabled = True

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column3("slug"), Column3(UneditableField("sku"))),
            Row(Column12("description")),
            Row(Column4("category"), Column4("tags"), Column4("size")),
            Row(Column6("channels"), Column6(InlineRadios("shipping"))),
            Row(
                Column3(PrependedText("price", "€")),
                Column3(AppendedText("warranty_months", "months")),
                Column3("stock"),
                Column3("rating"),
            ),
            Row(Column4("released_on"), Column4("published_at"), Column4("restock_at")),
            Row(Column4("is_active"), Column4(Switch("is_featured")), Column4("accent_color")),
            Row(Column4(FloatingField("contact_email")), Column4("website"), Column4("datasheet")),
            Fieldset("Internal", Row(Column12("internal_notes"))),
        ]


class ProductListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_product
    table_class = ProductTable
    filterset_class = ProductFilter
    formhelper_class = ProductFilterFormHelper
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["list", "filter", "create"]


class ProductDetailView(BreadcrumbMixin, DetailViewPermissionRequired):
    cv_viewset = cv_product
    template_name = "catalog/product_detail.html"


class ProductCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_product
    form_class = ProductForm
    cv_message_template_code = "Created »{{ object }}«"


class ProductUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_product
    form_class = ProductForm
    cv_cancel_keys = ["list", "detail"]
    cv_success_keys = ["list", "detail"]
    cv_message_template_code = "Updated »{{ object }}«"


class ProductDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_product
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_cancel_keys = ["list", "detail"]
    cv_success_keys = ["list"]  # never "detail": the object is gone
    cv_message_template_code = "Deleted »{{ object }}«"
