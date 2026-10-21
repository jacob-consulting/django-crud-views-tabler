"""A demo model whose fields cover one crispy render path each.

The point of this app is not the data: it is that an ``add product`` form puts every
django-crispy-forms template branch on one page, so the Tabler theme can be looked at
field by field (see ``docs/crispy_tabler_coverage.md``).
"""

import random
import string

from django.db import models


def new_sku() -> str:
    """A warehouse SKU. Generated here so the form can show it as an uneditable field."""
    return "SKU-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Category(models.Model):
    """Lookup for a single-choice ``<select>``."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Lookup for a multiple ``<select>`` and for the filter's inline checkboxes."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Channel(models.Model):
    """Lookup for a stacked checkbox list."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    class Size(models.TextChoices):
        S = "s", "Small"
        M = "m", "Medium"
        L = "l", "Large"

    class Shipping(models.TextChoices):
        STANDARD = "standard", "Standard"
        EXPRESS = "express", "Express"
        PICKUP = "pickup", "Pickup"

    # text
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, help_text="Lowercase, used in the product URL.")
    description = models.TextField(blank=True)
    sku = models.CharField(
        max_length=32, unique=True, default=new_sku, help_text="Assigned by the warehouse, not editable here."
    )

    # choices and relations
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    channels = models.ManyToManyField(Channel, blank=True, related_name="products")
    size = models.CharField(max_length=1, choices=Size.choices, default=Size.M)
    shipping = models.CharField(max_length=20, choices=Shipping.choices, default=Shipping.STANDARD)

    # numbers
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    warranty_months = models.PositiveIntegerField(default=24)
    stock = models.PositiveIntegerField(default=0)
    rating = models.PositiveSmallIntegerField(default=3, help_text="1 to 5.")

    # date and time
    released_on = models.DateField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    restock_at = models.TimeField(null=True, blank=True)

    # booleans
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Shown on the start page.")

    # the rest
    accent_color = models.CharField(max_length=7, default="#066fd1", help_text="Hex colour of the product badge.")
    contact_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    datasheet = models.FileField(upload_to="datasheets/", blank=True)
    internal_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def stock_badge(self):
        """Tabler colour for the stock badge."""
        if self.stock == 0:
            return "red"
        return "yellow" if self.stock < 10 else "green"
