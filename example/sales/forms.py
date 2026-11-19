"""Forms for customers, addresses and orders.

The wholesale-only fields follow ``Customer.kind`` through a shared ``ValueToggle`` in the server-side
conditional group and the crispy layout. Upstream infers native empty values when the group is inactive.
An order line's grind and bag size follow the selected product's kind through ``QuerysetConditions``.
"""

from catalog.models import Beans, Equipment, Product, Subscription
from crispy_forms.layout import HTML, Div, Row
from crud_views.lib.conditional import (
    ConditionalGroup,
    ConditionalGroupModelForm,
    QuerysetConditions,
    ToggleGroup,
    ValueToggle,
)
from crud_views.lib.crispy import Column2, Column3, Column4, Column6, Column12, CrispyForm, CrispyModelForm
from crud_views.lib.formsets import (
    CompactColumn,
    CompactLayout,
    FormSet,
    FormSets,
    Formsets,
    InlineFormSet,
)
from crud_views_widget_datetimepicker.widgets import DatePickerInput
from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.widgets import TypeaheadSelect
from django import forms
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Address, Customer, CustomerSubscription, Order, OrderLine, OrderState
from .permissions import can_on_customer

WHOLESALE_FIELDS = ["company", "vat_id", "price_tier", "payment_terms"]
WHOLESALE_TOGGLE = ValueToggle("kind", values=[Customer.Kind.WHOLESALE])


class CustomerForm(ConditionalGroupModelForm):
    submit_label = "Save"
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=WHOLESALE_TOGGLE,
            fields=WHOLESALE_FIELDS,
            required=["company", "price_tier", "payment_terms"],
        )
    ]

    class Meta:
        model = Customer
        fields = [
            "name",
            "kind",
            "contact_name",
            "email",
            "phone",
            "city",
            "country",
            "owner",
            *WHOLESALE_FIELDS,
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].empty_label = "Unassigned"

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column6("contact_name")),
            Row(Column4("email"), Column3("phone"), Column3("city"), Column2("country")),
            Row(Column4("owner")),
            Row(Column4("kind")),
            ToggleGroup(
                WHOLESALE_TOGGLE,
                Row(Column6("company"), Column6("vat_id")),
                Row(Column4("price_tier"), Column4("payment_terms")),
                legend="Wholesale terms",
            ),
            Row(Column12("notes")),
        ]


class AddressForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Address
        fields = ["label", "street", "zip_code", "city", "country", "is_default"]

    def get_layout_fields(self):
        return [
            Row(Column4("label")),
            Row(Column12("street")),
            Row(Column3("zip_code"), Column6("city"), Column3("country")),
            Row(Column12("is_default")),
        ]


# --------------------------------------------------------------------------- orders


# grind and bag size only apply to coffee: the product's kind (``Product.order_line_kind``, a class attribute of each
# polymorphic kind) is the conditional key, so a new coffee needs no code change; upstream disables the two cells in
# compact rows (also in rows added later) and clears them on save when the product is not coffee (finding 20)
LINE_PRODUCT = QuerysetConditions(
    "product", conditional_key="order_line_kind", keys=("beans", "equipment", "subscription", "product")
)
BEANS_ONLY = LINE_PRODUCT.when("beans")


class OrderLineForm(ConditionalGroupModelForm):
    cv_conditional_groups = [ConditionalGroup(toggle=BEANS_ONLY, fields=["grind", "bag_size"])]

    class Meta:
        model = OrderLine
        fields = ["product", "grind", "bag_size", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # beans and equipment on sale, plus whatever this line already holds (a retired coffee stays selectable)
        # (a union with the current product: a subscription line from "Run subscriptions" is neither beans nor
        # equipment)
        products = Product.objects.instance_of(Beans, Equipment).filter(is_active=True)
        if self.instance.pk:
            products = products | Product.objects.filter(pk=self.instance.product_id)
        self.fields["product"].queryset = products.distinct()
        for name in ("grind", "bag_size"):
            field = self.fields[name]
            field.choices = [("", "—"), *field.choices[1:]]  # no "Select an option" in a narrow column


class OrderLineInlineFormSet(InlineFormSet):
    def clean(self):
        super().clean()
        if self.instance.state != OrderState.CONFIRMED or any(self.errors):
            return
        kept = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if not kept:
            raise forms.ValidationError("A confirmed order needs at least one line item.")


OrderLineFormSet = inlineformset_factory(
    Order,
    OrderLine,
    formset=OrderLineInlineFormSet,
    form=OrderLineForm,
    fields=["product", "grind", "bag_size", "quantity"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

ORDER_FORMSETS = FormSets(
    formsets={
        "lines": FormSet(
            title="Line items",
            klass=OrderLineFormSet,
            fields=["product", "grind", "bag_size", "quantity"],
            pk_field="id",
            compact_layout=CompactLayout(
                columns=[
                    CompactColumn("product", span=4),
                    CompactColumn("grind", span=2),
                    CompactColumn("bag_size", span=2),
                    CompactColumn("quantity", span=2),
                ],
                controls_span=2,
            ),
        )
    }
)


class OrderForm(CrispyModelForm):
    """The nested order form: line items on the left, delivery and totals on the right (mockup tab "3 Order")."""

    submit_label = "Save"

    class Meta:
        model = Order
        fields = ["ship_to", "requested_roast_date", "notes"]
        widgets = {"requested_roast_date": DatePickerInput(), "notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer = self.cv_view.cv_get_parent_object()
        # only this customer's addresses: account managers hold view_address model-wide, so never the global set
        addresses = self.customer.addresses.all()
        self.fields["ship_to"].queryset = addresses
        self.fields["ship_to"].empty_label = "Choose an address"
        if not self.instance.pk:
            self.fields["ship_to"].initial = addresses.filter(is_default=True).first()

    def get_layout_fields(self):
        totals = render_to_string(
            "sales/snippets/order_totals.html",
            {"order": self.instance, "customer": self.customer, "form_hint": "Totals as last saved."},
        )
        return [
            Row(
                Div(Formsets(), css_class="col-lg-8"),
                Div(
                    HTML('<h3 class="card-title">Delivery</h3>'),
                    "ship_to",
                    "requested_roast_date",
                    "notes",
                    HTML(totals),
                    css_class="col-lg-4",
                ),
            )
        ]


class OrderStartForm(CrispyModelForm):
    """The top-level "new order" form: pick the customer, then the nested editor takes over."""

    submit_label = "Continue"
    customer = TypeaheadField(lookup="sales.customers", widget=TypeaheadSelect(), label="Customer")

    class Meta:
        model = Order
        fields = ["customer", "requested_roast_date"]
        widgets = {"requested_roast_date": DatePickerInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].bind(self.cv_view.request)

    def clean_customer(self):
        customer = self.cleaned_data["customer"]
        if not can_on_customer(self.cv_view.request.user, "change", customer):
            raise forms.ValidationError("You may not place orders for this customer.")
        return customer

    def get_layout_fields(self):
        return [Row(Column6("customer"), Column3("requested_roast_date"))]


class OrderDuplicateForm(CrispyForm):
    submit_label = "Duplicate"
    submit_icon = None

    requested_roast_date = forms.DateField(required=False, widget=DatePickerInput(), label="Requested roast date")

    def get_layout_fields(self):
        return [Row(Column4("requested_roast_date"))]


# --------------------------------------------------------------------------- subscriptions


class CustomerSubscriptionForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = CustomerSubscription
        fields = ["product", "started_on", "next_delivery", "is_active"]
        widgets = {"started_on": DatePickerInput(), "next_delivery": DatePickerInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        on_sale = Q(is_active=True) | Q(pk=self.instance.product_id) if self.instance.pk else Q(is_active=True)
        self.fields["product"].queryset = Subscription.objects.filter(on_sale)
        self.fields["product"].label = "Subscription"
        self.fields["is_active"].label = "Active"

    def get_layout_fields(self):
        return [
            Row(Column6("product")),
            Row(Column3("started_on"), Column3("next_delivery")),
            Row(Column12("is_active")),
        ]


class RunSubscriptionsForm(CrispyForm):
    submit_label = "Run subscriptions"
    submit_icon = None

    due = forms.DateField(
        widget=DatePickerInput(),
        label="Deliver up to",
        help_text=(
            "Every active subscription due on or before this date gets a draft order; each moves on by its interval."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["due"].initial = timezone.localdate()

    def get_layout_fields(self):
        return [Row(Column4("due"))]
