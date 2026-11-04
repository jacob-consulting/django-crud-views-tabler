"""CRUD views for customers: a Guardian ViewSet, so account managers only reach the customers granted to them.

Owner and Roasters hold model-level permissions, which the views accept (``cv_guardian_accept_global_perms``);
account managers hold none for viewing, only object grants, so the object check decides for them.
"""

import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.crispy import Column3, Column4, CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.view import ChildContextButton
from crud_views.lib.views import ListViewTableFilterMixin, ListViewTableMixin, MessageMixin
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import context_buttons_default
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_object_detail.lib import BadgeConfig, ObjectDetailMixin, x
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..forms import CustomerForm
from ..models import Customer
from ..permissions import grant_customer

cv_customer = GuardianViewSet(
    model=Customer,
    name="customer",
    icon_header="tabler:building-store",
    context_buttons=[
        *context_buttons_default(),
        ChildContextButton(key="orders", child_name="order", label_template_code="Orders"),
        ChildContextButton(key="addresses", child_name="address", label_template_code="Addresses"),
    ],
)


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass


class GlobalPermsMixin:
    cv_guardian_accept_global_perms = True


# --------------------------------------------------------------------------- list


class CustomerFilter(django_filters.FilterSet):
    kind = django_filters.ChoiceFilter(choices=Customer.Kind.choices, empty_label="Any kind")
    country = django_filters.ChoiceFilter(empty_label="Any country")
    owner = django_filters.ModelChoiceFilter(
        queryset=lambda request: get_user_model().objects.filter(customers__isnull=False).distinct(),
        empty_label="Any account manager",
        label="Account manager",
    )

    class Meta:
        model = Customer
        fields = ["kind", "country", "owner"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        countries = Customer.objects.exclude(country="").order_by("country").values_list("country", flat=True)
        self.filters["country"].extra["choices"] = [(c, c) for c in dict.fromkeys(countries)]


class CustomerFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column3("kind"), Column3("country"), Column4("owner")))


class CustomerTable(Table):
    id = LinkDetailColumn(verbose_name="#")
    name = tables.Column(verbose_name="Customer")
    kind = tables.Column()
    contact_name = tables.Column(verbose_name="Contact")
    city = tables.Column()
    country = tables.Column()
    owner = tables.Column(verbose_name="Account manager", default="")

    def render_name(self, record):
        return format_html(
            '<div class="d-flex align-items-center gap-2"><span class="avatar avatar-sm bg-{}-lt">{}</span>'
            "<span>{}</span></div>",
            record.avatar_color,
            record.initials,
            record.name,
        )

    def render_kind(self, record):
        color = "purple" if record.is_wholesale else "secondary"
        return format_html('<span class="badge bg-{}-lt">{}</span>', color, record.get_kind_display())


class CustomerListView(
    GlobalPermsMixin, BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, GuardianListViewPermissionRequired
):
    cv_viewset = cv_customer
    table_class = CustomerTable
    filterset_class = CustomerFilter
    formhelper_class = CustomerFilterFormHelper
    cv_list_actions = ["detail", "update", "delete"]
    cv_list_actions_inline = ["detail"]  # edit and delete go into the menu
    paginate_by = 15


# --------------------------------------------------------------------------- detail

_KIND_BADGE = BadgeConfig(
    color_map={"wholesale": "purple", "consumer": "secondary"},
    label_map={"wholesale": _("Wholesale"), "consumer": _("Consumer")},
    pill=True,
)

_DETAILS = [
    x("kind", badge=_KIND_BADGE),
    "contact_name",
    "email",
    "phone",
    "city",
    "country",
    "owner",
    x("created_at", title=_("Customer since")),
]
_WHOLESALE = [
    "company",
    "vat_id",
    x("price_tier_label", title=_("Price tier")),
    x("get_payment_terms_display", title=_("Payment terms")),
]

# One card, like the mockup; consumers have no wholesale terms to show
WHOLESALE_DISPLAY = [{"title": _("Details"), "icon": "tabler:building-store", "properties": [*_DETAILS, *_WHOLESALE, "notes"]}]
CONSUMER_DISPLAY = [{"title": _("Details"), "icon": "tabler:building-store", "properties": [*_DETAILS, "notes"]}]


class CustomerDetailView(GlobalPermsMixin, BreadcrumbMixin, ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_customer
    cv_object_detail_layout = "split-card"
    cv_header_template = "sales/snippets/customer_header.html"
    cv_paragraph_template = "sales/snippets/customer_paragraph.html"
    cv_context_actions = ["home", "update", "orders", "addresses", "delete"]
    cv_context_actions_inline = ["update", "orders", "addresses"]
    cv_property_display = WHOLESALE_DISPLAY

    @property
    def property_display(self):
        return WHOLESALE_DISPLAY if self.object.is_wholesale else CONSUMER_DISPLAY


# --------------------------------------------------------------------------- create / update / delete


class CustomerCreateView(
    GlobalPermsMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianCreateViewPermissionRequired
):
    cv_viewset = cv_customer
    form_class = CustomerForm
    cv_message_template_code = _("Created customer “{{ object }}”")

    def cv_form_valid(self, context: dict):
        form = context["form"]
        if form.instance.owner is None:
            form.instance.owner = self.request.user  # the creator looks after the customer unless told otherwise
        super().cv_form_valid(context)
        grant_customer(self.request.user, self.object)  # the creator may open and edit what they created


class CustomerUpdateView(
    GlobalPermsMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired
):
    cv_viewset = cv_customer
    form_class = CustomerForm
    cv_message_template_code = _("Updated customer “{{ object }}”")


class CustomerDeleteView(
    GlobalPermsMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired
):
    cv_viewset = cv_customer
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_show_related_objects = True
    cv_message_template_code = _("Deleted customer “{{ object }}”")
