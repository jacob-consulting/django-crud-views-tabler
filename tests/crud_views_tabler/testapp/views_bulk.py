"""Bulk selection on customers (upstream #392): a table and a card source and two destinations, on their own ViewSet so
the plain customer pages stay as they are."""

import django_tables2 as tables
from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.crispy import CrispyForm
from crud_views.lib.table import Table
from crud_views.lib.views import CardListViewPermissionRequired, ListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import ViewSet
from django import forms

from .models import Customer

cv_bulk_customer = ViewSet(
    model=Customer, name="bulk_customer", prefix="bulk-customer", icon_header="tabler:building-store"
)


class BulkCustomerTable(Table):
    name = tables.Column()
    country = tables.Column()

    class Meta:
        prefix = "c-"  # a prefixed table: its sort parameter is c-sort


class BulkCustomerListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_customer
    table_class = BulkCustomerTable
    cv_bulk_actions = ("clear_country", "set_country")
    cv_list_actions = []
    cv_context_actions = ["card"]


class BulkCustomerCardView(BulkSelectionMixin, CardListViewPermissionRequired):
    cv_viewset = cv_bulk_customer
    cv_bulk_actions = ("clear_country",)
    cv_context_actions = ["list"]
    cv_card_actions = []


class ClearCountryView(BulkFormViewPermissionRequired):
    """No input: the review lists eligible and blocked customers, then Confirm."""

    cv_viewset = cv_bulk_customer
    cv_key = "clear_country"
    cv_path = "clear-country"
    cv_permission = "change"
    cv_icon_action = "tabler:circle-x"
    cv_action_label_template_code = "Clear the country of the selected customers"
    cv_action_short_label_template_code = "Clear country"
    cv_success_key = "list"
    cv_success_keys = ["list", "card"]

    def cv_bulk_check(self, obj):
        return [] if obj.country else ["No country to clear."]

    def cv_form_valid(self, context):
        for customer in self.cv_bulk_objects:
            customer.country = ""
            customer.save(using=self.cv_get_db_alias(), update_fields=["country"])


class SetCountryForm(CrispyForm):
    submit_label = "Set"
    country = forms.CharField(max_length=100)

    def get_layout_fields(self):
        return ["country"]


class SetCountryView(BulkFormViewPermissionRequired):
    """With input: the review shows the action form."""

    cv_viewset = cv_bulk_customer
    cv_key = "set_country"
    cv_path = "set-country"
    cv_permission = "change"
    cv_icon_action = "tabler:map-pin"
    cv_action_label_template_code = "Set the country of the selected customers"
    cv_action_short_label_template_code = "Set country"
    form_class = SetCountryForm
    cv_success_key = "list"
    cv_message_template_code = "Country set for {{ view.cv_bulk_objects|length }} customers."

    def cv_form_valid(self, context):
        country = context["form"].cleaned_data["country"]
        for customer in self.cv_bulk_objects:
            customer.country = country
            customer.save(using=self.cv_get_db_alias(), update_fields=["country"])
