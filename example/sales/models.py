"""The roastery's customers: wholesale accounts (cafés, shops) and consumers, each with delivery addresses."""

from decimal import Decimal

from django.conf import settings
from django.db import models

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
    country = models.CharField(max_length=2, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers",
        verbose_name="Account manager",
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
    country = models.CharField(max_length=2)
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
