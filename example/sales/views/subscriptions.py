"""Customer subscriptions: a child ViewSet of the customer, a top-level list of all of them, and "Run subscriptions".

The nested views are gated on the URL's customer by upstream's ancestor guard, as for addresses and orders; the
top-level list filters by the same Guardian grants. Running the subscriptions creates orders for *every* customer, so
it has its own model permission (``run_customersubscription``, held by the Owner only); others see the button disabled
and get 403 on the URL.

The custom permission follows django-crud-views' documented recipe
(``docs/reference/custom_form_view.md#a-permission-of-its-own``): ``CustomerSubscription.Meta.permissions``
declares ``run_customersubscription`` and ``RunSubscriptionsView.cv_permission = "run"`` selects its ViewSet key.
"""

import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row
from crud_views.lib.crispy import Column3, CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ParentViewSet, ViewSet
from django.contrib import messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..forms import CustomerSubscriptionForm, RunSubscriptionsForm
from ..models import CustomerSubscription
from ..permissions import customers_for
from ..services import run_subscriptions
from .addresses import BreadcrumbMixin
from .customers import CustomerNavbarMixin

cv_subscription = ViewSet(
    model=CustomerSubscription,
    name="subscription",
    verbose_name=_("subscription"),
    verbose_name_plural=_("subscriptions"),
    parent=ParentViewSet(name="customer"),
    icon_header="subscription",
)

cv_all_subscriptions = ViewSet(
    model=CustomerSubscription,
    name="subscriptions",
    verbose_name=_("subscription"),
    verbose_name_plural=_("subscriptions"),
    icon_header="subscription",
)


class SubscriptionTableBase(Table):
    product = tables.Column(verbose_name="Subscription")
    interval = tables.Column(verbose_name="Interval", accessor="product__interval", order_by="product__interval")
    next_delivery = tables.DateColumn(verbose_name="Next delivery", format="d M Y")
    is_active = tables.Column(verbose_name="Status")

    def render_interval(self, record):
        return record.product.get_interval_display()

    def render_is_active(self, value):
        return format_html(
            '<span class="badge bg-{}-lt">{}</span>', "green" if value else "secondary", "Active" if value else "Paused"
        )


class SubscriptionTable(SubscriptionTableBase):
    class Meta:
        sequence = ("product", "interval", "next_delivery", "is_active", "...")


class AllSubscriptionsTable(SubscriptionTableBase):
    customer = tables.Column()

    class Meta:
        sequence = ("customer", "product", "interval", "next_delivery", "is_active", "...")
        exclude = ("actions",)  # edit them on the customer's page


class SubscriptionFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(
        field_name="is_active",
        label="Status",
        widget=django_filters.widgets.BooleanWidget(),
    )

    class Meta:
        model = CustomerSubscription
        fields = ["is_active"]


class SubscriptionFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column3("is_active")))


# --------------------------------------------------------------------------- nested


class SubscriptionListView(CustomerNavbarMixin, BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_subscription
    table_class = SubscriptionTable
    cv_list_actions = ["update", "delete"]
    cv_list_actions_inline = ["update"]

    def get_queryset(self):
        return super().get_queryset().select_related("customer", "product")


class SubscriptionCreateView(
    CustomerNavbarMixin,
    BreadcrumbMixin,
    CrispyViewMixin,
    MessageMixin,
    CreateViewParentMixin,
    CreateViewPermissionRequired,
):
    cv_viewset = cv_subscription
    form_class = CustomerSubscriptionForm
    cv_message_template_code = _("Subscribed {{ object.customer }} to {{ object.product }}")


class SubscriptionUpdateView(
    CustomerNavbarMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired
):
    cv_viewset = cv_subscription
    form_class = CustomerSubscriptionForm
    cv_message_template_code = _("Updated the subscription of {{ object.customer }}")


class SubscriptionDeleteView(
    CustomerNavbarMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired
):
    cv_viewset = cv_subscription
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted the subscription of {{ object.customer }}")


# --------------------------------------------------------------------------- top level


class AllSubscriptionsListView(
    BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired
):
    """Every subscription of the customers the user may see (Guardian grants decide, never ``Customer.owner``)."""

    cv_viewset = cv_all_subscriptions
    table_class = AllSubscriptionsTable
    filterset_class = SubscriptionFilter
    formhelper_class = SubscriptionFilterFormHelper
    cv_list_actions = []
    cv_context_actions = ["filter", "run"]
    cv_paragraph_template_code = _("Standing deliveries of every customer you may see")
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(customer__in=customers_for(self.request.user))
        return queryset.select_related("customer", "product")


class RunSubscriptionsView(BreadcrumbMixin, CrispyViewMixin, CustomFormNoObjectViewPermissionRequired):
    """Create a draft order for every due subscription, then report how many."""

    cv_viewset = cv_all_subscriptions
    cv_key = "run"
    cv_path = "run"
    cv_permission = "run"
    cv_inaccessible_actions = "disable"
    cv_icon_action = "run-subscriptions"
    form_class = RunSubscriptionsForm
    cv_success_key = "list"
    cv_cancel_key = "list"
    cv_context_actions = ["home"]
    cv_action_label_template_code = _("Run subscriptions")
    cv_action_short_label_template_code = _("Run subscriptions")
    cv_header_template_code = _("Run subscriptions")
    cv_paragraph_template_code = _("Create draft orders for every subscription that is due")

    def cv_form_valid(self, context: dict):
        orders = run_subscriptions(context["form"].cleaned_data["due"], self.request.user)
        count = len(orders)
        messages.success(self.request, f"Created {count} draft order{'' if count == 1 else 's'}")
