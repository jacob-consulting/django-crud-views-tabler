"""Forms for the roastery: lots, cupping sessions with their score rows, roast batches."""

from crispy_forms.layout import Row
from crud_views.lib.crispy import Column2, Column3, Column4, Column6, Column12, CrispyModelForm
from crud_views.lib.formsets import CompactColumn, CompactLayout, FormSet, FormSets, Formsets, InlineFormSet
from crud_views_widget_datetimepicker.widgets import DatePickerInput
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.utils import timezone
from sales.models import Order, OrderState

from .models import CuppingScore, CuppingSession, GreenLot, RoastBatch


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.get_username()


class GreenLotForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = GreenLot
        fields = [
            "code",
            "origin",
            "producer",
            "variety",
            "process",
            "harvest_year",
            "kg_purchased",
            "kg_on_hand",
            "price_per_kg",
            "arrived_on",
        ]
        widgets = {"arrived_on": DatePickerInput()}

    def get_layout_fields(self):
        return [
            Row(Column3("code"), Column3("origin"), Column6("producer")),
            Row(Column4("variety"), Column3("process"), Column2("harvest_year")),
            Row(Column3("kg_purchased"), Column3("kg_on_hand"), Column3("price_per_kg"), Column3("arrived_on")),
        ]


# --------------------------------------------------------------------------- cupping


class CuppingSessionForm(CrispyModelForm):
    """The session's date and notes; the score rows are the ``scores`` formset below them (mockup tab 5)."""

    submit_label = "Save"

    class Meta:
        model = CuppingSession
        fields = ["held_on", "notes"]
        widgets = {"held_on": DatePickerInput(), "notes": forms.Textarea(attrs={"rows": 2})}

    def get_layout_fields(self):
        return [Row(Column3("held_on"), Column6("notes")), Row(Column12(Formsets()))]


class CuppingScoreForm(CrispyModelForm):
    class Meta:
        model = CuppingScore
        fields = ["taster", *CuppingScore.ATTRIBUTES]
        widgets = {
            name: forms.NumberInput(attrs={"step": "0.25", "min": "0", "max": "10", "class": "form-control-sm"})
            for name in CuppingScore.ATTRIBUTES
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["taster"] = UserChoiceField(
            queryset=get_user_model().objects.order_by("first_name", "username"),
            label="Taster",
            empty_label="Choose a taster",
        )


CuppingScoreFormSet = inlineformset_factory(
    CuppingSession,
    CuppingScore,
    formset=InlineFormSet,
    form=CuppingScoreForm,
    fields=["taster", *CuppingScore.ATTRIBUTES],
    extra=2,
    can_delete=True,
    can_delete_extra=True,
)

CUPPING_FORMSETS = FormSets(
    formsets={
        "scores": FormSet(
            title="Scores",
            klass=CuppingScoreFormSet,
            fields=["taster", *CuppingScore.ATTRIBUTES],
            pk_field="id",
            compact_layout=CompactLayout(
                columns=[
                    CompactColumn("taster", span=3),
                    *(CompactColumn(name, span=1) for name in CuppingScore.ATTRIBUTES),
                ],
                controls_span=2,
            ),
        )
    }
)


# --------------------------------------------------------------------------- roast batches


class RoastBatchForm(CrispyModelForm):
    submit_label = "Save"
    roaster = UserChoiceField(queryset=get_user_model().objects.order_by("first_name", "username"))
    orders = forms.ModelMultipleChoiceField(
        queryset=Order.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 6}),
        help_text="The confirmed or roasted orders this batch fills. Hold Ctrl or Cmd to pick several.",
    )

    class Meta:
        model = RoastBatch
        fields = ["lot", "roasted_on", "profile", "green_kg", "roasted_kg", "roaster", "orders"]
        widgets = {"roasted_on": DatePickerInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # confirmed or roasted orders, plus whatever the batch already holds
        wanted = Q(state__in=[OrderState.CONFIRMED, OrderState.ROASTED])
        if self.instance.pk:
            wanted |= Q(roast_batches=self.instance)
        orders = self.fields["orders"]
        orders.queryset = Order.objects.filter(wanted).select_related("customer").distinct().order_by("-number")
        orders.label_from_instance = lambda order: f"{order} · {order.customer}"
        self.fields["lot"].queryset = GreenLot.objects.filter(kg_on_hand__gt=0) | GreenLot.objects.filter(
            pk=self.instance.lot_id
        )
        if not self.instance.pk:
            self.fields["roasted_on"].initial = timezone.localdate()
            self.fields["roaster"].initial = self.cv_view.request.user.pk

    def get_layout_fields(self):
        return [
            Row(Column4("lot"), Column3("roasted_on"), Column3("profile")),
            Row(Column3("green_kg"), Column3("roasted_kg"), Column4("roaster")),
            Row(Column6("orders")),
        ]
