"""The roastery's customers (wholesale accounts and consumers) with delivery addresses, and their orders."""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowModelMixin
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django_fsm import FSMField, TransitionNotAllowed, transition

CENT = Decimal("0.01")
AVATAR_COLORS = ["orange", "azure", "green", "purple", "pink", "teal", "red", "indigo", "cyan", "lime"]


class Customer(models.Model):
    class Kind(models.TextChoices):
        WHOLESALE = "wholesale", "Wholesale"
        CONSUMER = "consumer", "Consumer"

    class PriceTier(models.TextChoices):
        A = "A", "A (-20%)"
        B = "B", "B (-12%)"
        C = "C", "C (-5%)"

    class PaymentTerms(models.TextChoices):
        PREPAID = "prepaid", "Prepaid"
        NET_14 = "net_14", "Net 14"
        NET_30 = "net_30", "Net 30"
        NET_60 = "net_60", "Net 60"

    DISCOUNTS = {"A": Decimal("0.20"), "B": Decimal("0.12"), "C": Decimal("0.05")}

    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.CONSUMER)
    contact_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, blank=True, help_text="ISO country code, e.g. DE.")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers",
        verbose_name="Account manager",
        help_text="Gets access to this customer (view and change); the previous account manager loses it.",
    )
    # wholesale only
    company = models.CharField(max_length=150, blank=True)
    vat_id = models.CharField("VAT ID", max_length=30, blank=True)
    price_tier = models.CharField(max_length=1, choices=PriceTier.choices, null=True, blank=True)
    payment_terms = models.CharField(max_length=20, choices=PaymentTerms.choices, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_wholesale(self) -> bool:
        return self.kind == self.Kind.WHOLESALE

    @property
    def discount(self) -> Decimal:
        if not self.is_wholesale or not self.price_tier:
            return Decimal("0")
        return self.DISCOUNTS[self.price_tier]

    @property
    def price_tier_label(self) -> str:
        """The tier with its discount, e.g. ``B (-12%)``; empty for consumers."""
        return self.get_price_tier_display() if self.price_tier else ""

    @property
    def initials(self) -> str:
        words = [w for w in self.name.replace("&", " ").split() if w[:1].isalnum()]
        return "".join(w[0] for w in words[:2]).upper() or "?"

    @property
    def avatar_color(self) -> str:
        return AVATAR_COLORS[sum(map(ord, self.name)) % len(AVATAR_COLORS)]


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, help_text="E.g. Shop, Roastery door, Billing.")
    street = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, help_text="ISO country code, e.g. DE.")
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "label"]
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.label}: {self.street}, {self.zip_code} {self.city}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:  # one default per customer
            Address.objects.filter(customer=self.customer).exclude(pk=self.pk).update(is_default=False)


# --------------------------------------------------------------------------- orders


class OrderState(models.TextChoices):
    DRAFT = "draft", "Draft"
    CONFIRMED = "confirmed", "Confirmed"
    ROASTED = "roasted", "Roasted"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


EDITABLE_STATES = {OrderState.DRAFT, OrderState.CONFIRMED}
# The happy path, in order: the order page draws it as a steps bar.
ORDER_STEPS = [OrderState.DRAFT, OrderState.CONFIRMED, OrderState.ROASTED, OrderState.SHIPPED, OrderState.DELIVERED]


def may_change_order(order, user) -> bool:
    """Every transition but roasting: the model-level ``change_order`` plus change rights on the order's customer."""
    from .permissions import can_on_customer

    return user.has_perm("sales.change_order") and can_on_customer(user, "change", order.customer)


def may_roast_order(order, user) -> bool:
    """Roasters hold ``roast_order`` (and only view rights otherwise); whoever may change the order may roast it too."""
    return user.has_perm("sales.roast_order") or may_change_order(order, user)


class Order(WorkflowModelMixin, models.Model):
    STATE_CHOICES = OrderState
    STATE_BADGES = {
        OrderState.DRAFT: BadgeEnum.SECONDARY,
        OrderState.CONFIRMED: BadgeEnum.INFO,
        OrderState.ROASTED: BadgeEnum.WARNING,
        OrderState.SHIPPED: BadgeEnum.DARK,
        OrderState.DELIVERED: BadgeEnum.SUCCESS,
        OrderState.CANCELLED: BadgeEnum.DANGER,
    }
    FIRST_NUMBER = 1001

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    number = models.PositiveIntegerField(unique=True, editable=False)
    state = FSMField(default=OrderState.DRAFT, choices=OrderState.choices)
    ship_to = models.ForeignKey(Address, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    requested_roast_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-number"]
        permissions = [("roast_order", "Can mark orders as roasted")]

    def __str__(self):
        return f"Order #{self.number}"

    def save(self, *args, **kwargs):
        if self.number is None:
            last = Order.objects.aggregate(models.Max("number"))["number__max"]
            self.number = (last or self.FIRST_NUMBER - 1) + 1
        super().save(*args, **kwargs)

    # ----------------------------------------------------------------- money

    @property
    def subtotal(self) -> Decimal:
        return sum((line.line_total for line in self.lines.all()), Decimal("0.00"))

    @property
    def discount_amount(self) -> Decimal:
        return (self.subtotal * self.customer.discount).quantize(CENT, rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        return self.subtotal - self.discount_amount

    @property
    def line_count(self) -> int:
        return self.lines.count()

    # ----------------------------------------------------------------- workflow

    @property
    def is_editable(self) -> bool:
        return self.state in EDITABLE_STATES

    @property
    def steps(self) -> list[dict]:
        """The happy path for the steps bar: each step with ``active`` on the current state."""
        return [{"label": s.label, "active": s == self.state} for s in ORDER_STEPS]

    def confirm_problem(self) -> str | None:
        """Why the order cannot be confirmed yet, or None."""
        if not self.lines.exists():
            return "Add at least one line item before confirming the order."
        return None

    def workflow_check_transition(self, name, *, user):
        """Upstream's business hook: the workflow page shows Confirm disabled with the reason, and refuses it on
        POST."""
        if name == "wf_confirm" and (problem := self.confirm_problem()):
            raise ValidationError(problem)

    @transition(
        field=state,
        source=OrderState.DRAFT,
        target=OrderState.CONFIRMED,
        permission=may_change_order,
        custom={"label": "Confirm", "comment": WorkflowComment.NONE, "icon": "confirm", "variant": "success"},
    )
    def wf_confirm(self, request=None, by=None, comment=None):
        if problem := self.confirm_problem():  # workflow_check_transition refuses first; this guards direct calls
            raise TransitionNotAllowed(problem)

    @transition(
        field=state,
        source=OrderState.CONFIRMED,
        target=OrderState.ROASTED,
        permission=may_roast_order,
        custom={
            "label": "Mark roasted",
            "comment": WorkflowComment.OPTIONAL,
            "icon": "roasted",
            "variant": "warning",
        },
    )
    def wf_roast(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=OrderState.ROASTED,
        target=OrderState.SHIPPED,
        permission=may_change_order,
        custom={"label": "Ship", "comment": WorkflowComment.OPTIONAL, "icon": "shipped", "variant": "primary"},
    )
    def wf_ship(self, request=None, by=None, comment=None):
        self.shipped_at = timezone.now()

    @transition(
        field=state,
        source=OrderState.SHIPPED,
        target=OrderState.DELIVERED,
        permission=may_change_order,
        custom={
            "label": "Mark delivered",
            "comment": WorkflowComment.NONE,
            "icon": "delivered",
            "variant": "success",
        },
    )
    def wf_deliver(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=[OrderState.DRAFT, OrderState.CONFIRMED],
        target=OrderState.CANCELLED,
        permission=may_change_order,
        custom={
            "label": "Cancel order",
            "comment": WorkflowComment.REQUIRED,
            "icon": "cancelled",
            "variant": "danger",
        },
    )
    def wf_cancel(self, request=None, by=None, comment=None):
        pass


class OrderLine(models.Model):
    class Grind(models.TextChoices):
        WHOLE = "whole", "Whole bean"
        FILTER = "filter", "Filter"
        ESPRESSO = "espresso", "Espresso"

    class BagSize(models.TextChoices):
        G250 = "250g", "250 g"
        KG1 = "1kg", "1 kg"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="order_lines")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    grind = models.CharField(max_length=10, choices=Grind.choices, blank=True)
    bag_size = models.CharField(max_length=5, choices=BagSize.choices, blank=True)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, editable=False)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.quantity} × {self.product}"

    @property
    def is_beans(self) -> bool:
        # a plain FK returns the base Product row; ask polymorphic for the real class instead of loading it
        from catalog.models import Beans

        return self.product_id is not None and issubclass(self.product.get_real_instance_class(), Beans)

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price or Decimal("0.00")) * self.quantity

    def save(self, *args, **kwargs):
        if (
            not self.is_beans
        ):  # grind and bag size only mean something for coffee (also for lines written without a form)
            self.grind = self.bag_size = ""
        if self.unit_price is None or self.order.is_editable:  # prices are fixed once the order is roasted
            self.unit_price = self.product.price
        super().save(*args, **kwargs)


# --------------------------------------------------------------------------- subscriptions

INTERVAL_DAYS = {"weekly": 7, "biweekly": 14, "monthly": 30}


class CustomerSubscription(models.Model):
    """A customer's standing delivery of a ``catalog.Subscription`` product.

    "Run subscriptions" turns due ones into orders.
    """

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="subscriptions")
    product = models.ForeignKey("catalog.Subscription", on_delete=models.PROTECT, related_name="customer_subscriptions")
    started_on = models.DateField(default=timezone.localdate)
    next_delivery = models.DateField()
    is_active = models.BooleanField(default=True, help_text="Paused subscriptions are skipped by the run.")

    class Meta:
        ordering = ["next_delivery", "customer__name"]
        permissions = [("run_customersubscription", "Can run subscriptions (create orders for all due ones)")]

    def __str__(self):
        return f"{self.customer}: {self.product}"

    @property
    def interval_days(self) -> int:
        return INTERVAL_DAYS[self.product.interval]

    def advance(self) -> None:
        """Move ``next_delivery`` on by the product's interval (7, 14 or 30 days); the caller saves."""
        self.next_delivery += timedelta(days=self.interval_days)
