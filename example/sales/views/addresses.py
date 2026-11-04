"""Addresses are a plain child ViewSet of the customer.

Their own model-level permissions are not what protects them: every view first checks the URL's customer, so an
account manager reaches the addresses of granted customers only (view to read, change to write).
"""

import django_tables2 as tables
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..forms import AddressForm
from ..models import Address
from ..permissions import can_on_customer

cv_address = ViewSet(
    model=Address,
    name="address",
    icon_header="tabler:map-pin",
    parent=ParentViewSet(name="customer"),
)


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass


class CustomerGrantMixin:
    """Deny the view unless the user holds the needed permission on the customer in the URL."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            action = "view" if getattr(self, "cv_permission", "view") == "view" else "change"
            if not can_on_customer(request.user, action, self.cv_get_parent_object()):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AddressTable(Table):
    id = LinkDetailColumn(verbose_name="#")
    label = tables.Column()
    street = tables.Column()
    zip_code = tables.Column(verbose_name="ZIP")
    city = tables.Column()
    country = tables.Column()
    is_default = tables.Column(verbose_name="Default")

    def render_is_default(self, record):
        return mark_safe('<span class="badge bg-green-lt">Default</span>') if record.is_default else ""


class AddressListView(CustomerGrantMixin, BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_address
    table_class = AddressTable
    cv_list_actions = ["detail", "make_default", "update", "delete"]
    cv_list_actions_inline = ["detail"]


class AddressDetailView(CustomerGrantMixin, BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_address
    cv_property_display = [
        {
            "title": _("Address"),
            "icon": "tabler:map-pin",
            "properties": ["label", "street", "zip_code", "city", "country", "is_default", "customer"],
        }
    ]


class AddressCreateView(
    CustomerGrantMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_address
    form_class = AddressForm
    cv_message_template_code = _("Created address “{{ object.label }}”")


class AddressUpdateView(CustomerGrantMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_address
    form_class = AddressForm
    cv_message_template_code = _("Updated address “{{ object.label }}”")


class AddressDeleteView(CustomerGrantMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_address
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted address “{{ object.label }}”")


class AddressMakeDefaultView(CustomerGrantMixin, BreadcrumbMixin, MessageMixin, ActionViewPermissionRequired):
    cv_viewset = cv_address
    cv_key = "make_default"
    cv_path = "make_default"
    cv_permission = "change"
    cv_backend_only = True
    cv_icon_action = "tabler:star"
    cv_action_label_template_code = _("Make default")
    cv_action_short_label_template_code = _("Make default")
    cv_message_template_code = _("“{{ object.label }}” is now the default address")
    cv_message_template_error_code = _("Could not change the default address")

    def action(self, context) -> bool:
        self.object.is_default = True
        self.object.save()  # Address.save() clears the flag on the customer's other addresses
        return True
