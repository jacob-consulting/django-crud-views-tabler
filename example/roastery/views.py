"""CRUD views for the roastery.

``cv_lot`` (green lots) has ``cv_session`` (cupping sessions) as a child, so a session lives at
``/lot/<lot>/cupping/<session>/``; its scores are a formset on the session form. ``cv_batch`` (roast batches) is a
top-level ViewSet. Lots and batches are protected by the database (a batch protects its lot), and the lot's delete
page previews what goes with it.
"""

import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.crispy import Column3, Column4, CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.formsets import FormSetMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.view import ChildContextButton
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
from crud_views.lib.viewset import ParentViewSet, ViewSet, context_buttons_default
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired, x
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import CUPPING_FORMSETS, CuppingSessionForm, GreenLotForm, RoastBatchForm
from .models import CuppingSession, GreenLot, RoastBatch

cv_lot = ViewSet(
    model=GreenLot,
    name="lot",
    icon_header="lot",
    context_buttons=[
        *context_buttons_default(),
        ChildContextButton(key="sessions", child_name="cupping", label_template_code="Cupping sessions"),
    ],
)
cv_session = ViewSet(model=CuppingSession, name="cupping", icon_header="cupping", parent=ParentViewSet(name="lot"))
cv_batch = ViewSet(model=RoastBatch, name="batch", icon_header="batch")


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass


def score_badge(score) -> str:
    """A cupping score as a coloured badge: 85 and up is specialty-plus, 80 to 85 specialty, below that plain."""
    if score is None:
        return "—"
    color = "green" if score >= 85 else "lime" if score >= 80 else "orange"
    return format_html('<span class="badge bg-{}-lt">{}</span>', color, score)


# --------------------------------------------------------------------------- green lots


class LotTable(Table):
    code = LinkDetailColumn(verbose_name="Lot")
    origin = tables.Column()
    producer = tables.Column()
    process = tables.Column()
    harvest_year = tables.Column(verbose_name="Harvest")
    kg_on_hand = tables.Column(verbose_name="On hand", attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}})
    score = tables.Column(verbose_name="Cupping", accessor="average_score", orderable=False, empty_values=())

    def render_kg_on_hand(self, value):
        return f"{value:,.1f} kg"

    def render_process(self, record):
        return record.get_process_display()

    def render_score(self, record):
        return score_badge(record.average_score)


class LotFilter(django_filters.FilterSet):
    process = django_filters.ChoiceFilter(
        choices=GreenLot._meta.get_field("process").choices, empty_label="Any process"
    )
    harvest_year = django_filters.ChoiceFilter(empty_label="Any harvest", label="Harvest")

    class Meta:
        model = GreenLot
        fields = ["process", "harvest_year"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        years = GreenLot.objects.order_by("-harvest_year").values_list("harvest_year", flat=True).distinct()
        self.filters["harvest_year"].extra["choices"] = [(y, y) for y in years]


class LotFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column3("process"), Column3("harvest_year")))


class LotListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_lot
    table_class = LotTable
    filterset_class = LotFilter
    formhelper_class = LotFilterFormHelper
    cv_list_actions = ["detail", "update", "delete"]
    cv_list_actions_inline = ["detail"]
    paginate_by = 15

    def get_queryset(self):
        return super().get_queryset().select_related("origin").prefetch_related("sessions__scores")


class LotDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    """Upstream's accordion, first group open (#328); customers use `split-card`, products `tabs-vertical`.
    Sessions are a child list, one button away."""

    cv_viewset = cv_lot
    cv_object_detail_layout = "accordion"
    cv_context_actions = ["home", "update", "sessions", "delete"]
    cv_context_actions_inline = ["update", "sessions"]
    cv_property_display = [
        {
            "title": _("Origin and producer"),
            "icon": "origin",
            "properties": ["origin", "producer", "variety", "process", "harvest_year"],
        },
        {
            "title": _("Stock and price"),
            "icon": "stock",
            "properties": [
                x("kg_purchased", title=_("Purchased (kg)")),
                x("kg_on_hand", title=_("On hand (kg)")),
                x("price_per_kg", title=_("Price per kg (€)")),
                "arrived_on",
            ],
        },
        {
            "title": _("Cupping"),
            "icon": "cupping",
            "properties": [
                x("average_score", title=_("Average score")),
                x("session_count", title=_("Sessions")),
                x("beans_names", title=_("Sold as")),
            ],
        },
    ]

    def session_count(self, instance):
        return instance.sessions.count()

    def beans_names(self, instance):
        return ", ".join(b.name for b in instance.beans.all()) or "—"


class LotCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_lot
    form_class = GreenLotForm
    cv_message_template_code = _("Created lot {{ object }}")


class LotUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_lot
    form_class = GreenLotForm
    cv_message_template_code = _("Updated lot {{ object }}")


class LotDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    """Previews the cupping sessions that go with the lot; a lot with roast batches cannot be deleted at all."""

    cv_viewset = cv_lot
    form_class = CrispyDeleteForm
    cv_show_related_objects = True
    cv_message_template_code = _("Deleted lot {{ object }}")


# --------------------------------------------------------------------------- cupping sessions


class SessionTable(Table):
    held_on = LinkDetailColumn(verbose_name="Date")
    tasters = tables.Column(verbose_name="Tasters", accessor="pk", orderable=False)
    average = tables.Column(verbose_name="Average", accessor="pk", orderable=False)
    notes = tables.Column(orderable=False)

    def render_held_on(self, record):
        return f"{record.held_on:%d %b %Y}"

    def render_tasters(self, record):
        return len(record.scores.all())

    def render_average(self, record):
        return score_badge(record.average)


class SessionListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_session
    table_class = SessionTable
    cv_list_actions = ["detail", "update", "delete"]
    cv_list_actions_inline = ["detail", "update"]
    cv_header_template_code = _("Cupping sessions")

    def get_queryset(self):
        return super().get_queryset().prefetch_related("scores")


class SessionDetailView(BreadcrumbMixin, DetailViewPermissionRequired):
    """The scores as a table with each taster's total and the session average (mockup tab 5)."""

    cv_viewset = cv_session
    template_name = "roastery/session_detail.html"
    cv_header_template_code = _("Cupping session · {{ object.held_on|date:'j M Y' }}")
    cv_paragraph_template_code = _(
        "Lot {{ object.lot.code }} · {{ object.lot.origin }} · {{ object.lot.kg_on_hand }} kg on hand"
    )
    cv_context_actions = ["home", "update", "delete"]
    cv_context_actions_inline = ["update"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scores"] = self.object.scores.select_related("taster")
        context["average_badge"] = score_badge(self.object.average)
        return context


class SessionCreateView(
    BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_session
    form_class = CuppingSessionForm
    cv_formsets = CUPPING_FORMSETS
    cv_success_key = "detail"
    cv_header_template_code = _("New cupping session")
    cv_paragraph_template_code = _("The date, and each taster's scores")
    cv_message_template_code = _("Created {{ object }}")


class SessionUpdateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_session
    form_class = CuppingSessionForm
    cv_formsets = CUPPING_FORMSETS
    cv_success_key = "detail"
    cv_cancel_keys = ["list", "detail"]
    cv_message_template_code = _("Updated {{ object }}")


class SessionDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_session
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_show_related_objects = True
    cv_message_template_code = _("Deleted {{ object }}")


# --------------------------------------------------------------------------- roast batches


class BatchTable(Table):
    id = LinkDetailColumn(verbose_name="#")
    roasted_on = tables.DateColumn(verbose_name="Roasted", format="d M Y")
    lot = tables.Column()
    profile = tables.Column()
    green_kg = tables.Column(verbose_name="Green", attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}})
    roasted_kg = tables.Column(
        verbose_name="Roasted kg", attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}}
    )
    loss = tables.Column(
        verbose_name="Loss",
        accessor="weight_loss_pct",
        orderable=False,
        attrs={"td": {"class": "text-end"}, "th": {"class": "text-end"}},
    )
    roaster = tables.Column()

    def render_id(self, record):
        return f"#{record.pk}"

    def render_profile(self, record):
        return record.get_profile_display()

    def render_loss(self, value):
        return f"{value} %" if value is not None else "—"

    def render_roaster(self, record):
        return record.roaster.get_full_name() or record.roaster.get_username()


class BatchFilter(django_filters.FilterSet):
    lot = django_filters.ModelChoiceFilter(queryset=GreenLot.objects.all(), empty_label="Any lot")
    profile = django_filters.ChoiceFilter(choices=RoastBatch.Profile.choices, empty_label="Any profile")

    class Meta:
        model = RoastBatch
        fields = ["lot", "profile"]


class BatchFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("lot"), Column3("profile")))


class BatchListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_batch
    table_class = BatchTable
    filterset_class = BatchFilter
    formhelper_class = BatchFilterFormHelper
    cv_list_actions = ["detail", "update", "delete"]
    cv_list_actions_inline = ["detail"]
    paginate_by = 15

    def get_queryset(self):
        return super().get_queryset().select_related("lot", "roaster")


class BatchDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_batch
    cv_property_display = [
        {
            "title": _("Roast"),
            "icon": "batch",
            "properties": [
                "lot",
                "roasted_on",
                x("get_profile_display", title=_("Profile")),
                "roaster",
                "green_kg",
                "roasted_kg",
                x("loss_label", title=_("Weight loss")),
            ],
        },
        {"title": _("Orders"), "icon": "order", "properties": ["orders"]},
    ]

    def loss_label(self, instance):
        loss = instance.weight_loss_pct
        return f"{loss} %" if loss is not None else "—"


class BatchCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_batch
    form_class = RoastBatchForm
    cv_message_template_code = _("Created {{ object }}")


class BatchUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_batch
    form_class = RoastBatchForm
    cv_message_template_code = _("Updated {{ object }}")


class BatchDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_batch
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted {{ object }}")
