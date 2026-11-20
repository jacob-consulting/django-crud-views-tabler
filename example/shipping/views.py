"""Courier tracking: a read-only Resource (the fake courier API) with a list and a detail page.

Permission: ``sales.view_order``, which Owner, Account managers and Roasters all hold model-wide. It lets Sam into the
list; ``Shipment.cv_get_items`` then scopes the rows to the customers Sam is granted, so another rep's tracking number
is a 404.
"""

import django_tables2 as tables
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.resource import ResourceViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import ViewSet
from django.urls import reverse
from django.utils.html import format_html

from .resources import Shipment

cv_shipment = ViewSet(
    model=Shipment,
    name="shipment",
    icon_header="shipment",
    resource_permissions={"view": "sales.view_order"},
)

STATUS_BADGES = {"in_transit": ("azure", "In transit"), "delivered": ("green", "Delivered")}


def status_badge(status: str):
    color, label = STATUS_BADGES[status]
    return format_html('<span class="badge bg-{}-lt">{}</span>', color, label)


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass


class ShipmentTable(Table):
    tracking_number = LinkDetailColumn(verbose_name="Tracking number")
    order_number = tables.Column(verbose_name="Order")
    customer_name = tables.Column(verbose_name="Customer")
    carrier = tables.Column()
    status = tables.Column()
    shipped_at = tables.DateColumn(verbose_name="Shipped", format="d M Y")
    eta = tables.DateColumn(verbose_name="ETA", format="d M Y")

    class Meta:
        exclude = ("actions",)

    def render_order_number(self, record):
        url = reverse("order-detail", kwargs={"customer_pk": record.customer_pk, "pk": record.order_pk})
        return format_html('<a href="{}">#{}</a>', url, record.order_number)

    def render_status(self, record):
        return status_badge(record.status)


class ShipmentListView(BreadcrumbMixin, ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_shipment
    table_class = ShipmentTable
    cv_list_actions = []
    cv_context_actions = []
    paginate_by = 20


class ShipmentDetailView(BreadcrumbMixin, ResourceViewMixin, DetailViewPermissionRequired):
    cv_viewset = cv_shipment
    template_name = "shipping/shipment_detail.html"
    cv_header_template_code = "{{ object }}"
    cv_paragraph_template_code = "{{ object.carrier }} · order #{{ object.order_number }} · {{ object.customer_name }}"
    cv_context_actions = ["home"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shipment = self.object
        context["status_badge"] = status_badge(shipment.status)
        context["order_url"] = reverse(
            "order-detail", kwargs={"customer_pk": shipment.customer_pk, "pk": shipment.order_pk}
        )
        context["events"] = list(reversed(shipment.events))  # newest first
        return context
