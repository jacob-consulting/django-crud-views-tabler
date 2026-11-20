"""Order views beyond CRUD: the workflow step, the printable packing slip and "duplicate as a new draft".

Permissions for the workflow follow upstream's documented opt-in recipe (``docs/reference/workflow_view.md`` in
django-crud-views): the view itself only needs ``view_order`` (Roasters hold no ``change_order``); which steps a user
may take is decided per transition by django-fsm's ``permission=`` (``may_change_order`` / ``may_roast_order`` in
``models.py``), and the workflow action shows disabled when the user has no step left to take. Each step is its own
submit button (``cv_transition_presentation = "buttons"``); ``Order.workflow_check_transition`` disables Confirm,
with the reason, while the order has no lines.
"""

from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.views import DetailViewPermissionRequired, MessageMixin
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views_workflow.lib import WorkflowForm, WorkflowViewPermissionRequired
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..forms import OrderDuplicateForm
from ..models import Order, OrderLine
from .addresses import BreadcrumbMixin
from .customers import CustomerNavbarMixin
from .orders import ORDER_CONTEXT_ACTIONS, cv_order


class OrderWorkflowView(
    CustomerNavbarMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, WorkflowViewPermissionRequired
):
    cv_viewset = cv_order
    form_class = WorkflowForm
    cv_transition_presentation = "buttons"
    cv_permission = "view"  # the per-transition permissions decide (see the module docstring)
    cv_inaccessible_actions = "disable"
    cv_success_key = "detail"
    cv_context_actions = ORDER_CONTEXT_ACTIONS
    cv_context_actions_inline = ["update", "packing_slip"]
    cv_message_template_code = _("{{ object }} is now {{ object.state_name|lower }}")

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        return obj is None or obj.workflow_has_any_possible_transition(user)


class OrderPackingSlipView(CustomerNavbarMixin, BreadcrumbMixin, DetailViewPermissionRequired):
    cv_viewset = cv_order
    cv_key = "packing_slip"
    cv_path = "packing-slip"
    template_name = "sales/packing_slip.html"
    cv_icon_action = "packing-slip"
    cv_action_label_template_code = _("Packing slip")
    cv_action_short_label_template_code = _("Packing slip")
    cv_header_template_code = _("Packing slip · {{ object }}")
    cv_paragraph_template_code = _("Print it and put it in the box")
    cv_context_actions = ["detail", "packing_slip"]


class OrderDuplicateView(
    CustomerNavbarMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired
):
    """A new draft for the same customer with the same lines, at today's prices."""

    cv_viewset = cv_order
    cv_key = "duplicate"
    cv_path = "duplicate"
    cv_permission = "add"
    cv_icon_action = "duplicate"
    form_class = OrderDuplicateForm
    cv_action_label_template_code = _("Duplicate")
    cv_action_short_label_template_code = _("Duplicate")
    cv_header_template_code = _("Duplicate {{ object }}")
    cv_paragraph_template_code = _("Start a new draft with the same line items")
    cv_message_template_code = _("Created {{ view.duplicate }} from {{ object }}")
    cv_context_actions = ORDER_CONTEXT_ACTIONS
    cv_context_actions_inline = ["update", "packing_slip"]

    def cv_form_valid(self, context: dict):
        source = self.object
        self.duplicate = Order.objects.create(
            customer=source.customer,
            ship_to=source.ship_to,
            notes=source.notes,
            requested_roast_date=context["form"].cleaned_data["requested_roast_date"],
        )
        for line in source.lines.all():
            OrderLine.objects.create(
                order=self.duplicate,
                product=line.product,
                quantity=line.quantity,
                grind=line.grind,
                bag_size=line.bag_size,
            )

    def get_success_url(self) -> str:
        return reverse("order-detail", kwargs={"customer_pk": self.duplicate.customer_id, "pk": self.duplicate.pk})
