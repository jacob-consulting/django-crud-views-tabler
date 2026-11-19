"""The roastery's green coffee and what is done with it: lots, cupping sessions with scores, roast batches."""

from decimal import ROUND_HALF_UP, Decimal

from catalog.models import Beans, Origin
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

HUNDREDTH = Decimal("0.01")
TENTH = Decimal("0.1")
SCORE_STEP = Decimal("0.25")


def validate_score_step(value):
    """Scores move in quarter points, as on a cupping form."""
    if value % SCORE_STEP:
        raise ValidationError("Scores go in steps of 0.25.")


class GreenLot(models.Model):
    """A purchase of green (unroasted) coffee from one producer, identified by its lot ``code`` (e.g. CO-24-017)."""

    code = models.CharField(max_length=20, unique=True, help_text="Country, harvest year, number: e.g. CO-24-017.")
    origin = models.ForeignKey(Origin, on_delete=models.PROTECT, related_name="lots")
    producer = models.CharField(max_length=150)
    variety = models.CharField(max_length=100)
    process = models.CharField(max_length=10, choices=Beans.Process.choices, default=Beans.Process.WASHED)
    harvest_year = models.PositiveSmallIntegerField()
    kg_purchased = models.DecimalField(
        "kg purchased", max_digits=8, decimal_places=1, validators=[MinValueValidator(0)]
    )
    kg_on_hand = models.DecimalField("kg on hand", max_digits=8, decimal_places=1, validators=[MinValueValidator(0)])
    price_per_kg = models.DecimalField(
        "price per kg (€)", max_digits=7, decimal_places=2, validators=[MinValueValidator(0)]
    )
    arrived_on = models.DateField()

    class Meta:
        ordering = ["-arrived_on", "code"]

    def __str__(self):
        return self.code

    def clean(self):
        super().clean()
        if self.kg_on_hand is not None and self.kg_purchased is not None and self.kg_on_hand > self.kg_purchased:
            raise ValidationError({"kg_on_hand": "More on hand than was purchased."})

    @property
    def average_score(self) -> Decimal | None:
        """The mean total of every score given to this lot, over all its sessions."""
        totals = [score.total for session in self.sessions.all() for score in session.scores.all()]
        return mean(totals)


def mean(values) -> Decimal | None:
    values = list(values)
    if not values:
        return None
    return (sum(values) / len(values)).quantize(HUNDREDTH, ROUND_HALF_UP)


class CuppingSession(models.Model):
    """A tasting of one lot on one day; each taster's scores are a ``CuppingScore`` row."""

    lot = models.ForeignKey(GreenLot, on_delete=models.CASCADE, related_name="sessions")
    held_on = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-held_on", "-pk"]

    def __str__(self):
        return f"Cupping {self.held_on:%d %b %Y}"

    @property
    def average(self) -> Decimal | None:
        """The mean of the tasters' totals."""
        return mean(score.total for score in self.scores.all())


class CuppingScore(models.Model):
    """One taster's scores for one session, SCA style.

    Seven attributes (aroma, flavor, acidity, body, aftertaste, balance, overall) are scored 0 to 10 in steps of
    0.25. ``total`` is their sum plus 30 base points, so a cup scored 8.00 throughout totals 86.00 and the maximum
    is 100. A taster scores a session once.
    """

    ATTRIBUTES = ("aroma", "flavor", "acidity", "body", "aftertaste", "balance", "overall")
    BASE_POINTS = Decimal("30")

    session = models.ForeignKey(CuppingSession, on_delete=models.CASCADE, related_name="scores")
    taster = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cupping_scores")
    aroma = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10), validate_score_step]
    )
    flavor = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10), validate_score_step]
    )
    acidity = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10), validate_score_step]
    )
    body = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10), validate_score_step]
    )
    aftertaste = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10), validate_score_step]
    )
    balance = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10), validate_score_step]
    )
    overall = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10), validate_score_step]
    )

    class Meta:
        ordering = ["pk"]
        constraints = [models.UniqueConstraint(fields=["session", "taster"], name="roastery_score_one_per_taster")]

    def __str__(self):
        return f"{self.taster} · {self.total}"

    @property
    def total(self) -> Decimal:
        return self.BASE_POINTS + sum((getattr(self, name) for name in self.ATTRIBUTES), Decimal("0"))


class RoastBatch(models.Model):
    """One roast of a green lot; the orders it fills are linked."""

    class Profile(models.TextChoices):
        LIGHT = "light", "Light filter"
        MEDIUM = "medium", "Medium omni"
        ESPRESSO = "espresso", "Espresso"
        DARK = "dark", "Dark"

    lot = models.ForeignKey(GreenLot, on_delete=models.PROTECT, related_name="batches")
    roasted_on = models.DateField()
    profile = models.CharField(max_length=10, choices=Profile.choices, default=Profile.MEDIUM)
    green_kg = models.DecimalField(
        "green kg", max_digits=6, decimal_places=1, validators=[MinValueValidator(Decimal("0.1"))]
    )
    roasted_kg = models.DecimalField("roasted kg", max_digits=6, decimal_places=1, validators=[MinValueValidator(0)])
    roaster = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="roast_batches")
    orders = models.ManyToManyField("sales.Order", blank=True, related_name="roast_batches")

    class Meta:
        ordering = ["-roasted_on", "-pk"]
        verbose_name_plural = "roast batches"

    def __str__(self):
        return f"Batch #{self.pk} · {self.lot} · {self.roasted_on:%d %b %Y}"

    def clean(self):
        super().clean()
        if self.green_kg is not None and self.roasted_kg is not None and self.roasted_kg > self.green_kg:
            raise ValidationError({"roasted_kg": "Roasting cannot add weight: this is more than the green weight."})
        if self.lot_id and self.green_kg is not None:
            available = self._available_kg()
            if self.green_kg > available:
                raise ValidationError({"green_kg": f"Lot {self.lot.code} has only {available} kg on hand."})

    def _available_kg(self) -> Decimal:
        """What this batch may draw from its lot: the stock, plus the weight it already holds there."""
        available = GreenLot.objects.get(pk=self.lot_id).kg_on_hand
        if self.pk:
            previous = (
                RoastBatch.objects.filter(pk=self.pk, lot_id=self.lot_id).values_list("green_kg", flat=True).first()
            )
            available += previous or 0
        return available

    # The green weight leaves the lot's ``kg_on_hand`` when a batch is saved and returns when it is deleted, in one
    # transaction with the lot row locked. (``QuerySet.delete()`` and ``bulk_create`` bypass this.)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk and (old := RoastBatch.objects.filter(pk=self.pk).first()):
                GreenLot.objects.filter(pk=old.lot_id).update(kg_on_hand=models.F("kg_on_hand") + old.green_kg)
            lot = GreenLot.objects.select_for_update().get(pk=self.lot_id)
            if self.green_kg > lot.kg_on_hand:
                raise ValidationError({"green_kg": f"Lot {lot.code} has only {lot.kg_on_hand} kg on hand."})
            GreenLot.objects.filter(pk=lot.pk).update(kg_on_hand=models.F("kg_on_hand") - self.green_kg)
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            GreenLot.objects.filter(pk=self.lot_id).update(kg_on_hand=models.F("kg_on_hand") + self.green_kg)
            return super().delete(*args, **kwargs)

    @property
    def weight_loss_pct(self) -> Decimal | None:
        """What the roast took out of the bean, in percent of the green weight (12.0 kg to 10.2 kg is 15.0)."""
        if not self.green_kg:
            return None
        return ((self.green_kg - self.roasted_kg) / self.green_kg * 100).quantize(TENTH, ROUND_HALF_UP)
