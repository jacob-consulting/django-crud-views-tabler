"""CRUD views for the catalog.

``cv_product`` is a polymorphic ViewSet: the card list is the landing page (the ``list`` view), a table list sits
beside it, and creating a product is two steps (pick the kind, then that kind's form). ``cv_category`` is an ordered
lookup with up/down views.
"""

import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.crispy import Column3, Column4, CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.view import CardAction
from crud_views.lib.views import (
    CardListViewPermissionRequired,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    OrderedUpDownPermissionRequired,
    OrderedUpViewPermissionRequired,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import BadgeConfig, ObjectDetailMixin, ObjectDetailViewPermissionRequired, x
from crud_views_polymorphic.lib import (
    PolymorphicCreateSelectViewPermissionRequired,
    PolymorphicCreateViewPermissionRequired,
    PolymorphicDeleteViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
    PolymorphicUpdateViewPermissionRequired,
)
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from .forms import POLYMORPHIC_FORMS, CategoryForm, ProductContentTypeForm
from .models import Beans, Category, Equipment, Product, Subscription

cv_product = ViewSet(model=Product, name="product", icon_header="product")
cv_category = ViewSet(model=Category, name="category", icon_header="category")


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass


# --------------------------------------------------------------------------- products: lists


def product_types(request=None):
    return ContentType.objects.filter(
        app_label="catalog", model__in=[m._meta.model_name for m in (Beans, Equipment, Subscription)]
    ).order_by("model")


class ProductFilter(django_filters.FilterSet):
    type = django_filters.ModelChoiceFilter(
        field_name="polymorphic_ctype", queryset=product_types, label="Type", empty_label="Any type"
    )
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all(), empty_label="Any category")
    is_active = django_filters.BooleanFilter(label="Active")

    class Meta:
        model = Product
        fields = ["type", "category", "is_active"]


class ProductFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("type"), Column4("category"), Column3("is_active")))


# Cards first, table second: upstream documents this recipe (docs/reference/card-list-view.md, #325). The card list
# takes `cv_key = "list"` and `cv_path = ""`, the table gets its own key and `cv_home_key = "list"`; no new API.
class ProductCardListView(BreadcrumbMixin, ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_product
    cv_key = "list"  # the card list is the landing page; the table is `table`
    cv_path = ""
    filterset_class = ProductFilter
    formhelper_class = ProductFilterFormHelper
    cv_context_actions = ["list", "table", "filter", "create_select"]
    cv_card_template = "catalog/product_card.html"
    cv_card_container_class = "col-md-6 col-lg-4"
    paginate_by = 12
    cv_order_fields = [
        ("name", _("Name A-Z")),
        ("-name", _("Name Z-A")),
        ("price", _("Price low-high")),
        ("-price", _("Price high-low")),
    ]
    cv_order_default = "name"
    cv_card_actions = [
        CardAction(key="detail", label=_("Details"), variant="primary", flex=True),
        CardAction(key="update", label_mode="icon"),
        CardAction(key="delete", label_mode="icon", variant="tertiary"),
    ]


class ProductTable(Table):
    id = LinkDetailColumn(verbose_name="#")
    name = tables.Column()
    type = tables.Column(accessor="polymorphic_ctype__model", verbose_name="Type")
    sku = tables.Column()
    category = tables.Column()
    price = tables.Column(attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}})
    stock = tables.Column(attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}})
    is_active = tables.BooleanColumn(verbose_name="Active")

    def render_type(self, record):
        return record.type_label


# The table beside the cards: the other half of upstream's cards-first recipe (#325), see ProductCardListView.
class ProductTableListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_product
    cv_key = "table"
    cv_path = "table"
    cv_home_key = "list"
    table_class = ProductTable
    filterset_class = ProductFilter
    formhelper_class = ProductFilterFormHelper
    cv_context_actions = ["list", "table", "filter", "create_select"]
    cv_list_actions = ["detail", "update", "delete"]
    cv_icon_action = "table-view"


# --------------------------------------------------------------------------- products: create / update / delete


class ProductCreateSelectView(BreadcrumbMixin, CrispyViewMixin, PolymorphicCreateSelectViewPermissionRequired):
    cv_viewset = cv_product
    model = Product
    form_class = ProductContentTypeForm


class ProductCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, PolymorphicCreateViewPermissionRequired):
    cv_viewset = cv_product
    model = Product
    polymorphic_forms = POLYMORPHIC_FORMS
    cv_message_template_code = _("Created product “{{ object }}”")


class ProductUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, PolymorphicUpdateViewPermissionRequired):
    cv_viewset = cv_product
    model = Product
    polymorphic_forms = POLYMORPHIC_FORMS
    cv_message_template_code = _("Updated product “{{ object }}”")
    cv_success_keys = ["list", "detail"]


class ProductDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, PolymorphicDeleteViewPermissionRequired):
    cv_viewset = cv_product
    model = Product
    form_class = CrispyDeleteForm
    cv_show_related_objects = True  # names the order lines that protect a product
    cv_message_template_code = _("Deleted product “{{ object }}”")


# --------------------------------------------------------------------------- products: detail

_ACTIVE_BADGE = BadgeConfig(
    color_map={True: "success", False: "secondary"}, label_map={True: _("Active"), False: _("Inactive")}, pill=True
)


def commerce(model):
    """The Commerce group; the stock row only for kinds that are stocked (``show_stock``), as on the card."""
    stock = ["stock"] if model.show_stock else []
    return {
        "title": _("Commerce"),
        "icon": "pricing",
        "properties": ["sku", "price", *stock, x("is_active", badge=_ACTIVE_BADGE), "category"],
    }


ABOUT = {"title": _("About"), "icon": "about", "properties": ["description"]}

PROPERTY_DISPLAY = {
    Beans: [
        {
            "title": _("Coffee"),
            "icon": "beans",
            "properties": [
                "origin",
                x("green_lot", title=_("Green lot")),
                "process",
                x("altitude_m", title=_("Altitude (m)")),
                "roast_level",
                "flavor_notes",
            ],
        },
        commerce(Beans),
        ABOUT,
    ],
    Equipment: [
        {"title": _("Equipment"), "icon": "equipment", "properties": ["brand", "warranty_months", "weight_kg"]},
        commerce(Equipment),
        ABOUT,
    ],
    Subscription: [
        {
            "title": _("Subscription"),
            "icon": "subscription",
            "properties": [
                "interval",
                "bags_per_delivery",
                "bag_size",
            ],
        },
        commerce(Subscription),
        ABOUT,
    ],
}


class ProductDetailView(BreadcrumbMixin, ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_product
    model = Product
    cv_property_display = PROPERTY_DISPLAY


# --------------------------------------------------------------------------- categories


class CategoryTable(Table):
    id = LinkDetailColumn(verbose_name="#")
    name = tables.Column()


class CategoryListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_category
    table_class = CategoryTable
    cv_list_actions = ["detail", "update", "delete", "up", "down"]


class CategoryDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_category
    cv_property_display = [
        {
            "title": _("Category"),
            "icon": "category",
            "properties": ["name", {"path": "product_count", "title": _("Products")}],
        }
    ]

    def product_count(self, instance):
        return instance.products.count()


class CategoryCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_category
    form_class = CategoryForm
    cv_message_template_code = _("Created category “{{ object }}”")


class CategoryUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_category
    form_class = CategoryForm
    cv_message_template_code = _("Updated category “{{ object }}”")


class CategoryDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_category
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted category “{{ object }}”")
    cv_show_related_objects = True


class CategoryUpView(BreadcrumbMixin, MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_category
    cv_message_template_code = _("Moved category “{{ object }}” up")


class CategoryDownView(BreadcrumbMixin, MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_category
    cv_message_template_code = _("Moved category “{{ object }}” down")
