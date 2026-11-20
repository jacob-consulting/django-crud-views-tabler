"""Orders: a child ViewSet of the customer (the full editor) and a top-level ViewSet (all orders, and "new order").

Like addresses, the nested views are gated on the URL's customer by upstream's ancestor guard: an account manager
reaches the orders of granted customers only. The top-level list filters by the same Guardian grants, never by
``Customer.owner``. An order can be edited or deleted only while it is a draft or confirmed; afterwards the actions
show disabled and their URLs answer 403. The workflow, packing slip and duplicate views live in ``order_actions.py``.
"""

import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row
from crud_views.lib.crispy import Column3, CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.formsets import FormSetMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.view import ContextButton
from crud_views.lib.views import (
    CreateViewParentMixin,
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
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet, context_buttons_default
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..forms import ORDER_FORMSETS, OrderForm, OrderStartForm
from ..models import Order, OrderState
from ..permissions import customers_for
from .addresses import BreadcrumbMixin
from .customers import CustomerNavbarMixin

cv_order = ViewSet(
    model=Order,
    name="order",
    parent=ParentViewSet(name="customer"),
    icon_header="order",
    ancestor_policy=AncestorPolicy(
        actions={
            "duplicate": AncestorPermissions(nearest="change", higher="view"),
            "workflow": AncestorPermissions(nearest="view", higher="view"),
        }
    ),
    context_buttons=[
        *context_buttons_default(),
        ContextButton(key="packing_slip", key_target="packing_slip"),
    ],
)

cv_all_orders = ViewSet(model=Order, name="orders", icon_header="order")

ORDER_CONTEXT_ACTIONS = ["home", "update", "workflow", "packing_slip", "duplicate", "delete"]


def order_is_editable(obj) -> bool:
    """The state gate of update and delete: only drafts and confirmed orders change."""
    return obj is None or obj.is_editable


class EditableOrderMixin:
    cv_inaccessible_actions = "disable"  # shown greyed out on a shipped order, not hidden

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        return order_is_editable(obj)


# --------------------------------------------------------------------------- tables


class OrderTableBase(Table):
    created_at = tables.DateColumn(verbose_name="Date", format="d M Y")
    line_count = tables.Column(verbose_name="Items", orderable=False, empty_values=())
    total = tables.Column(
        orderable=False, empty_values=(), attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}}
    )
    state = tables.Column(verbose_name="Status", accessor="state_badge", order_by="state")

    def render_total(self, record):
        return f"€ {record.total:,.2f}"


class OrderTable(OrderTableBase):
    number = LinkDetailColumn(verbose_name="#")

    class Meta:
        sequence = ("number", "created_at", "line_count", "total", "state", "...")


class AllOrdersTable(OrderTableBase):
    number = tables.Column(verbose_name="#")
    customer = tables.Column()

    class Meta:
        sequence = ("number", "customer", "created_at", "line_count", "total", "state", "...")
        exclude = ("actions",)  # no row actions: the number links into the customer's order pages

    def render_number(self, record):
        url = reverse("order-detail", kwargs={"customer_pk": record.customer_id, "pk": record.pk})
        return format_html('<a href="{}">{}</a>', url, record.number)


class OrderFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(choices=OrderState.choices, empty_label="Any status", label="Status")

    class Meta:
        model = Order
        fields = ["state"]


class OrderFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column3("state")))


# --------------------------------------------------------------------------- nested: list / detail


class OrderListView(
    CustomerNavbarMixin, BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired
):
    cv_viewset = cv_order
    table_class = OrderTable
    filterset_class = OrderFilter
    formhelper_class = OrderFilterFormHelper
    cv_list_actions = ["detail", "update", "workflow", "duplicate", "delete"]
    cv_list_actions_inline = ["detail", "update"]

    def get_queryset(self):
        return super().get_queryset().select_related("customer").prefetch_related("lines")


class OrderDetailView(CustomerNavbarMixin, BreadcrumbMixin, DetailViewPermissionRequired):
    """Steps bar, line items, delivery card with totals, history; the possible transitions are header buttons."""

    cv_viewset = cv_order
    template_name = "sales/order_detail.html"
    cv_header_template_code = "{{ object }}"  # the template adds the state badge to the page title (not to <title>)
    cv_paragraph_template_code = "{{ object.customer }} · created {{ object.created_at|date:'d M Y' }}"
    cv_context_actions = ORDER_CONTEXT_ACTIONS
    cv_context_actions_inline = ["update", "packing_slip"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context["transitions"] = [
            {"name": t.name, "label": t.custom.get("label", t.name), **t.custom}
            for t in order.get_available_user_state_transitions(self.request.user)
        ]
        if order.state in (OrderState.SHIPPED, OrderState.DELIVERED):  # the courier's tracking page (shipping app)
            context["shipment_url"] = reverse("shipment-detail", kwargs={"pk": f"ACME{order.number:08d}"})
        context["workflow_url"] = reverse("order-workflow", kwargs={"customer_pk": order.customer_id, "pk": order.pk})
        return context


# --------------------------------------------------------------------------- nested: create / update / delete


class OrderCreateView(
    CustomerNavbarMixin,
    BreadcrumbMixin,
    CrispyViewMixin,
    FormSetMixin,
    MessageMixin,
    CreateViewParentMixin,
    CreateViewPermissionRequired,
):
    cv_viewset = cv_order
    form_class = OrderForm
    cv_formsets = ORDER_FORMSETS
    cv_success_key = "detail"
    cv_header_template_code = _("New order for {{ parent_object }}")
    cv_paragraph_template_code = _("A draft order: add its line items and the delivery")
    cv_message_template_code = _("Created {{ object }}")


class OrderUpdateView(
    CustomerNavbarMixin,
    EditableOrderMixin,
    BreadcrumbMixin,
    CrispyViewMixin,
    FormSetMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
):
    cv_viewset = cv_order
    form_class = OrderForm
    cv_formsets = ORDER_FORMSETS
    cv_success_key = "detail"
    cv_cancel_keys = ["list", "detail"]
    cv_context_actions = ORDER_CONTEXT_ACTIONS
    cv_context_actions_inline = ["update", "packing_slip"]
    cv_header_template_code = _("Edit {{ object }}")
    cv_paragraph_template_code = _("Line items, delivery and notes; totals update when you save")
    cv_message_template_code = _("Updated {{ object }}")


class OrderDeleteView(
    CustomerNavbarMixin,
    EditableOrderMixin,
    BreadcrumbMixin,
    CrispyViewMixin,
    MessageMixin,
    DeleteViewPermissionRequired,
):
    cv_viewset = cv_order
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted {{ object }}")


# --------------------------------------------------------------------------- top level: all orders, new order


class AllOrdersListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    """Every order the user may see: Guardian grants on the customer decide (all of them with model-level rights)."""

    cv_viewset = cv_all_orders
    table_class = AllOrdersTable
    filterset_class = OrderFilter
    formhelper_class = OrderFilterFormHelper
    cv_list_actions = []
    cv_context_actions = ["filter", "create"]
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(customer__in=customers_for(self.request.user))
        return queryset.select_related("customer").prefetch_related("lines")


class AllOrdersCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    """Pick a customer (type-ahead), then continue in the nested editor to add the lines."""

    cv_viewset = cv_all_orders
    form_class = OrderStartForm
    cv_message_template_code = _("Created {{ object }} for {{ object.customer }}; add its line items")
    cv_header_template_code = _("New order")
    cv_paragraph_template_code = _("Choose the customer; the line items follow on the next page")

    def cv_form_valid(self, context: dict):
        form = context["form"]
        form.instance.ship_to = form.cleaned_data["customer"].addresses.filter(is_default=True).first()
        super().cv_form_valid(context)

    def get_success_url(self) -> str:
        return reverse("order-update", kwargs={"customer_pk": self.object.customer_id, "pk": self.object.pk})
