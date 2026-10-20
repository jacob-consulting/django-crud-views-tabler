import django_tables2 as tables
import django_filters
from crispy_forms.layout import Layout, Row
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.crispy import Column4, Column6, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.table.columns import NaturalTimeColumn
from crud_views.lib.view import CardAction
from crud_views.lib.views import (
    CardListViewPermissionRequired,
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

from .models import Customer

cv_customer = ViewSet(model=Customer, name="customer", icon_header="tabler:building-store")

class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass


class CustomerTable(Table):
    id = LinkDetailColumn(verbose_name="#")
    name = tables.Column()
    company = tables.Column()
    status = tables.TemplateColumn(
        template_code='<span class="badge bg-{{ record.status_badge }}-lt">{{ record.get_status_display }}</span>'
    )
    country = tables.Column()
    revenue = tables.Column(attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}})
    created_at = NaturalTimeColumn(verbose_name="Created")


class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    country = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Customer
        fields = ["name", "status", "country"]


class CustomerFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("name"), Column4("status"), Column4("country")))


class CustomerForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Customer
        fields = ["name", "company", "email", "country", "status", "revenue", "notes"]

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column6("company")),
            Row(Column6("email"), Column6("country")),
            Row(Column6("status"), Column6("revenue")),
            Row(Column12("notes")),
        ]


class CustomerListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_customer
    table_class = CustomerTable
    filterset_class = CustomerFilter
    formhelper_class = CustomerFilterFormHelper
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["list", "card", "filter", "create"]


class CustomerCardListView(BreadcrumbMixin, ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_customer
    filterset_class = CustomerFilter
    formhelper_class = CustomerFilterFormHelper
    cv_context_actions = ["list", "card", "filter", "create"]
    cv_card_template = "customers/customer_card.html"
    cv_card_container_class = "col-sm-6 col-lg-4"
    cv_card_actions = [
        CardAction(key="detail", label="Open", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]
    cv_order_fields = [("name", "Name"), ("revenue", "Revenue"), ("created_at", "Created")]
    paginate_by = 12


class CustomerDetailView(BreadcrumbMixin, DetailViewPermissionRequired):
    cv_viewset = cv_customer
    template_name = "customers/customer_detail.html"


class CustomerCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_customer
    form_class = CustomerForm
    cv_cancel_keys = ["list", "card"]
    cv_success_keys = ["list", "card"]
    cv_message_template_code = "Created »{{ object }}«"


class CustomerUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_customer
    form_class = CustomerForm
    cv_cancel_keys = ["list", "card", "detail"]
    cv_success_keys = ["list", "card", "detail"]
    cv_message_template_code = "Updated »{{ object }}«"


class CustomerDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_customer
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_cancel_keys = ["list", "card", "detail"]
    cv_success_keys = ["list", "card"]  # never "detail": the object is gone
    cv_message_template_code = "Deleted »{{ object }}«"
