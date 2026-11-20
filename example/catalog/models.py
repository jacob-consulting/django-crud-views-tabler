"""The roastery's catalog: one polymorphic ``Product`` with a table per kind (beans, equipment, subscription).

The kinds share the commerce fields on ``Product``; each adds what only it has. ``card_color`` and ``card_icon`` are the
type's look on the card list (a Tabler colour name, a semantic icon name from ``config.icons``).
"""

from decimal import Decimal

from django.db import models
from ordered_model.models import OrderedModel
from polymorphic.models import PolymorphicModel


class Origin(models.Model):
    country = models.CharField(max_length=2, help_text="ISO country code, e.g. CO.")
    region = models.CharField(max_length=100)

    class Meta:
        ordering = ["country", "region"]
        constraints = [models.UniqueConstraint(fields=["country", "region"], name="catalog_origin_unique")]

    def __str__(self):
        return f"{self.country} · {self.region}"


class FlavorNote(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, default="secondary", help_text="A Tabler colour name, e.g. orange.")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(OrderedModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta(OrderedModel.Meta):
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(PolymorphicModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    sku = models.CharField("SKU", max_length=30, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField("active", default=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    description = models.TextField(blank=True)

    card_color = "secondary"
    card_icon = "product"
    show_stock = True  # subscriptions are not stocked
    # the conditional key of an order line's product select (sales.forms.LINE_PRODUCT): only beans take grind and bag
    order_line_kind = "product"

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_beans(self) -> bool:
        return isinstance(self, Beans)

    @property
    def type_label(self) -> str:
        return self._meta.verbose_name.title()

    @property
    def stock_label(self) -> str:
        if self.stock == 0:
            return "sold out"
        return f"{self.stock} left" if self.stock < 10 else "in stock"

    @property
    def stock_color(self) -> str:
        return "red" if self.stock == 0 else "orange" if self.stock < 10 else "green"

    @property
    def card_subtitle(self) -> str:
        return ""

    @property
    def card_corner(self) -> str:
        return ""

    @property
    def price_suffix(self) -> str:
        return ""


class Beans(Product):
    class Process(models.TextChoices):
        WASHED = "washed", "Washed"
        NATURAL = "natural", "Natural"
        HONEY = "honey", "Honey"
        ANAEROBIC = "anaerobic", "Anaerobic"

    class RoastLevel(models.TextChoices):
        LIGHT = "light", "Light"
        MEDIUM = "medium", "Medium"
        DARK = "dark", "Dark"

    origin = models.ForeignKey(Origin, on_delete=models.PROTECT, related_name="beans")
    process = models.CharField(max_length=10, choices=Process.choices, default=Process.WASHED)
    altitude_m = models.PositiveIntegerField("altitude (m)", null=True, blank=True)
    roast_level = models.CharField(max_length=10, choices=RoastLevel.choices, default=RoastLevel.MEDIUM)
    flavor_notes = models.ManyToManyField(FlavorNote, blank=True, related_name="beans")
    green_lot = models.ForeignKey(
        "roastery.GreenLot",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="beans",
        verbose_name="green lot",
        help_text="The lot this coffee is roasted from.",
    )

    card_color = "orange"
    order_line_kind = "beans"
    card_icon = "beans"

    class Meta:
        verbose_name = "beans"
        verbose_name_plural = "beans"

    @property
    def card_subtitle(self) -> str:
        parts = [self.get_process_display()]
        if self.altitude_m:
            parts.append(f"{self.altitude_m:,} m")
        parts.append(f"{self.get_roast_level_display()} roast")
        return " · ".join(parts)

    @property
    def card_corner(self) -> str:
        return f"{self.origin.country} · {self.origin.region}"

    @property
    def price_suffix(self) -> str:
        return "/ 250 g"


class Equipment(Product):
    brand = models.CharField(max_length=100)
    warranty_months = models.PositiveIntegerField(default=24)
    weight_kg = models.DecimalField("weight (kg)", max_digits=6, decimal_places=2, null=True, blank=True)

    card_color = "azure"
    order_line_kind = "equipment"
    card_icon = "equipment"

    class Meta:
        verbose_name = "equipment"
        verbose_name_plural = "equipment"

    @property
    def card_subtitle(self) -> str:
        parts = [f"Warranty {self.warranty_months} months"]
        if self.weight_kg:
            parts.append(f"{self.weight_kg.normalize():f} kg")
        return " · ".join(parts)

    @property
    def card_corner(self) -> str:
        return self.brand


class Subscription(Product):
    class Interval(models.TextChoices):
        WEEKLY = "weekly", "Every week"
        BIWEEKLY = "biweekly", "Every 2 weeks"
        MONTHLY = "monthly", "Every month"

    class BagSize(models.TextChoices):
        G250 = "250g", "250 g"
        KG1 = "1kg", "1 kg"

    interval = models.CharField(max_length=10, choices=Interval.choices, default=Interval.MONTHLY)
    bags_per_delivery = models.PositiveIntegerField(default=2)
    bag_size = models.CharField(max_length=5, choices=BagSize.choices, default=BagSize.G250)

    card_color = "purple"
    order_line_kind = "subscription"
    card_icon = "subscription"
    show_stock = False

    class Meta:
        verbose_name = "subscription"
        verbose_name_plural = "subscriptions"

    @property
    def card_subtitle(self) -> str:
        return f"{self.bags_per_delivery} × {self.get_bag_size_display()}"

    @property
    def card_corner(self) -> str:
        return self.get_interval_display().lower()

    @property
    def price_suffix(self) -> str:
        return "/ delivery"
