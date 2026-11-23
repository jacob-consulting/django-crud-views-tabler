"""Bulk actions on all orders (django-crud-views #392): select orders on the table or the cards, then "Mark roasted"
or "Cancel".

Each action is one of the order's django-fsm transitions, run through crud_views_workflow's ``run_transition``, so the
history and the per-transition permissions are the workflow page's. A selected order in the wrong state is blocked
with the reason on the review page; an order the user may not move (django-fsm's ``permission=``) or outside their
customers counts as unavailable. "Mark roasted" needs ``roast_order`` (Roasters hold it) and runs at once when every
selected order is confirmed; "Cancel" needs ``change_order`` and asks for the reason the workflow requires.
"""

from crud_views.lib.bulk import BulkFormViewPermissionRequired
from crud_views.lib.crispy import CrispyForm
from crud_views_workflow.lib import run_transition
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_fsm import can_proceed

from ..permissions import customers_for
from .addresses import BreadcrumbMixin
from .orders import cv_all_orders


class OrderTransitionBulkMixin:
    """Run the transition ``order_transition`` on every eligible selected order (a mixin: a view with a ViewSet
    registers itself, so the shared base has none)."""

    order_transition: str = ""
    order_state_reason: str = ""  # the blocked reason, with {state}
    cv_success_key = "list"
    cv_success_keys = ["list", "card"]
    cv_atomic = True

    def get_queryset(self):
        # the same scope as the source lists: a filter on the list alone would be no authorization gate
        queryset = super().get_queryset().filter(customer__in=customers_for(self.request.user))
        return queryset.select_related("customer")

    def cv_bulk_has_permission(self, obj):
        # the transition's permission= alone; has_transition_perm would also refuse an order in the wrong state, which
        # then showed as "unavailable" instead of blocked with the reason below
        transitions = [t for t in obj.get_all_state_transitions() if t.name == self.order_transition]
        return any(t.has_perm(obj, self.request.user) for t in transitions)

    def cv_bulk_check(self, obj):
        if not can_proceed(getattr(obj, self.order_transition)):
            return [self.order_state_reason.format(state=obj.get_state_display().lower())]
        try:
            obj.workflow_check_transition(self.order_transition, user=self.request.user)
        except ValidationError as error:
            return list(error.messages)
        return []

    def get_transition_comment(self, context) -> str | None:
        return None

    def cv_form_valid(self, context):
        comment = self.get_transition_comment(context)
        for order in self.cv_bulk_objects:
            run_transition(order, self.order_transition, user=self.request.user, comment=comment)


class OrderBulkRoastView(OrderTransitionBulkMixin, BreadcrumbMixin, BulkFormViewPermissionRequired):
    cv_viewset = cv_all_orders
    cv_key = "bulk_roast"
    cv_path = "bulk-roast"
    cv_permission = "roast"  # the model's custom roast_order permission
    cv_icon_action = "roasted"
    cv_action_label_template_code = _("Mark the selected orders roasted")
    cv_action_short_label_template_code = _("Mark roasted")
    cv_bulk_confirm = False  # straight through when every order is confirmed; the review only for blocked ones
    order_transition = "wf_roast"
    order_state_reason = _("Only confirmed orders can be roasted; this one is {state}.")
    cv_message_template_code = (
        "{% load i18n %}{% blocktranslate count count=view.cv_bulk_objects|length %}"
        "{{ count }} order marked roasted.{% plural %}{{ count }} orders marked roasted."
        "{% endblocktranslate %}"
    )


class OrderBulkCancelForm(CrispyForm):
    submit_label = _("Confirm")
    comment = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Saved in each order's history, as on the workflow page."),
    )

    def get_layout_fields(self):
        return ["comment"]


class OrderBulkCancelView(OrderTransitionBulkMixin, BreadcrumbMixin, BulkFormViewPermissionRequired):
    cv_viewset = cv_all_orders
    cv_key = "bulk_cancel"
    cv_path = "bulk-cancel"
    cv_permission = "change"
    cv_icon_action = "cancelled"
    cv_action_variant = "danger"  # the destructive bulk action, styled by the theme's bulk:danger (upstream #400)
    cv_action_label_template_code = _("Cancel the selected orders")
    cv_action_short_label_template_code = _("Cancel orders")
    form_class = OrderBulkCancelForm
    order_transition = "wf_cancel"
    order_state_reason = _("Only draft and confirmed orders can be cancelled; this one is {state}.")
    cv_message_template_code = (
        "{% load i18n %}{% blocktranslate count count=view.cv_bulk_objects|length %}"
        "{{ count }} order cancelled.{% plural %}{{ count }} orders cancelled."
        "{% endblocktranslate %}"
    )

    def get_transition_comment(self, context):
        return context["form"].cleaned_data["comment"]
