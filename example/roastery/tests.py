import random
from datetime import date
from decimal import Decimal

from catalog.models import Beans, Origin
from catalog.seed import seed as seed_catalog
from dashboard.seed import seed as seed_dashboard
from django.test import TestCase
from django.urls import reverse
from sales.models import OrderState
from sales.seed import seed as seed_sales

from .models import CuppingScore, CuppingSession, GreenLot, RoastBatch
from .seed import seed as seed_roastery

SCORE_FIELDS = ["aroma", "flavor", "acidity", "body", "aftertaste", "balance", "overall"]


class RoasteryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.world = {}
        rng = random.Random(1)
        seed_dashboard(rng, cls.world)
        seed_catalog(rng, cls.world)
        seed_sales(rng, cls.world)
        seed_roastery(rng, cls.world)
        cls.users = cls.world["users"]
        cls.lot = GreenLot.objects.create(
            code="XX-24-001",
            origin=Origin.objects.first(),
            producer="Test farm",
            variety="Bourbon",
            process="washed",
            harvest_year=2024,
            kg_purchased=Decimal("600"),
            kg_on_hand=Decimal("600"),
            price_per_kg=Decimal("9.50"),
            arrived_on=date(2026, 1, 5),
        )

    def login(self, username="alex"):
        self.client.login(username=username, password="demo")

    @staticmethod
    def score_row(taster, value="8.00"):
        return {"taster": str(taster.pk), **dict.fromkeys(SCORE_FIELDS, value)}

    @staticmethod
    def formset_post(prefix, rows, initial=0):
        data = {
            f"{prefix}-TOTAL_FORMS": str(len(rows)),
            f"{prefix}-INITIAL_FORMS": str(initial),
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        for i, row in enumerate(rows):
            data.update({f"{prefix}-{i}-{key}": value for key, value in row.items()})
        return data

    def session_post(self, rows, prefix="scores-None-0", **fields):
        return {"held_on": "2026-11-04", "notes": "", **fields, **self.formset_post(prefix, rows)}


class SeedTests(RoasteryTestCase):
    def test_seed_shape(self):
        self.assertGreaterEqual(GreenLot.objects.exclude(pk=self.lot.pk).count(), 6)
        self.assertTrue(CuppingScore.objects.filter(taster=self.users["sam"]).exists())
        self.assertTrue(RoastBatch.objects.filter(orders__isnull=False).exists())
        for batch in RoastBatch.objects.prefetch_related("orders"):
            for order in batch.orders.all():
                self.assertNotIn(order.state, {OrderState.DRAFT, OrderState.CANCELLED})  # batches fill live orders
        self.assertTrue(Beans.objects.filter(green_lot__isnull=False).exists())
        self.assertTrue(
            RoastBatch.objects.filter(orders__state=OrderState.CONFIRMED).exists()
            or RoastBatch.objects.filter(orders__state=OrderState.ROASTED).exists()
        )


class CuppingTests(RoasteryTestCase):
    def test_compact_score_rows_have_shared_headings_and_associated_labels(self):
        self.login()
        create_url = reverse("cupping-create", kwargs={"lot_pk": self.lot.pk})
        create_html = self.client.get(create_url).content.decode()
        self.assertEqual(create_html.count('class="row cv-formset-compact-headings"'), 1)
        self.assertEqual(create_html.count("cv-formset-row-compact"), 2)
        for label in ("Taster", *[name.title() for name in SCORE_FIELDS]):
            self.assertIn(label, create_html)
        for field in ("taster", "aroma"):
            self.assertRegex(create_html, rf'<label[^>]+for="id_scores-None-0-0-{field}"')

        session = CuppingSession.objects.create(lot=self.lot, held_on=date(2026, 11, 4))
        CuppingScore.objects.create(
            session=session, taster=self.users["alex"], **{field: Decimal("8") for field in SCORE_FIELDS}
        )
        update_url = reverse("cupping-update", kwargs={"lot_pk": self.lot.pk, "pk": session.pk})
        update_html = self.client.get(update_url).content.decode()
        self.assertEqual(update_html.count('class="row cv-formset-compact-headings"'), 1)
        self.assertIn("cv-formset-row-compact", update_html)

        invalid = {**self.score_row(self.users["kim"]), "aroma": "10.5"}
        response = self.client.post(create_url, self.session_post([invalid]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cv-formset-compact-headings")
        self.assertContains(response, 'value="10.5"')
        self.assertContains(response, "less than or equal to 10")

    def test_cupping_scores_formset(self):
        self.login()
        url = reverse("cupping-create", kwargs={"lot_pk": self.lot.pk})
        self.assertContains(self.client.get(url), 'name="scores-None-0-TOTAL_FORMS"')
        rows = [self.score_row(self.users["alex"], "8.00"), self.score_row(self.users["kim"], "7.50")]
        response = self.client.post(url, self.session_post(rows))
        self.assertEqual(response.status_code, 302)
        session = CuppingSession.objects.get(lot=self.lot)
        self.assertEqual(session.scores.count(), 2)
        alex = session.scores.get(taster=self.users["alex"])
        self.assertEqual(alex.total, Decimal("86.00"))  # seven attributes at 8.00 + 30
        self.assertEqual(session.average, Decimal("84.25"))  # (86.00 + 82.50) / 2
        self.assertEqual(self.lot.average_score, Decimal("84.25"))
        self.assertRedirects(response, reverse("cupping-detail", kwargs={"lot_pk": self.lot.pk, "pk": session.pk}))

    def test_duplicate_taster_rejected(self):
        self.login()
        url = reverse("cupping-create", kwargs={"lot_pk": self.lot.pk})
        rows = [self.score_row(self.users["alex"]), self.score_row(self.users["alex"], "7.00")]
        response = self.client.post(url, self.session_post(rows))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CuppingSession.objects.filter(lot=self.lot).exists())
        self.assertIn("duplicate", response.content.decode().lower())

    def test_score_out_of_range_rejected(self):
        self.login()
        url = reverse("cupping-create", kwargs={"lot_pk": self.lot.pk})
        for bad in ("10.5", "8.10", "-1"):
            row = {**self.score_row(self.users["alex"]), "aroma": bad}
            response = self.client.post(url, self.session_post([row]))
            self.assertEqual(response.status_code, 200, bad)
            self.assertFalse(CuppingSession.objects.filter(lot=self.lot).exists(), bad)
        row = {**self.score_row(self.users["alex"]), "aroma": "10.5"}
        self.assertContains(self.client.post(url, self.session_post([row])), "less than or equal to 10")

    def test_update_edits_scores(self):
        session = CuppingSession.objects.create(lot=self.lot, held_on=date(2026, 11, 4))
        score = CuppingScore.objects.create(
            session=session, taster=self.users["alex"], **{f: Decimal("8") for f in SCORE_FIELDS}
        )
        self.login()
        url = reverse("cupping-update", kwargs={"lot_pk": self.lot.pk, "pk": session.pk})
        prefix = f"scores-{session.pk}-0"
        row = {**self.score_row(self.users["alex"], "9.00"), "id": str(score.pk), "session": str(session.pk)}
        response = self.client.post(url, self.session_post([row], prefix=prefix) | {f"{prefix}-INITIAL_FORMS": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(session.scores.get().total, Decimal("93.00"))

    def test_breadcrumb_two_levels(self):
        session = CuppingSession.objects.create(lot=self.lot, held_on=date(2026, 11, 4))
        self.login()
        html = self.client.get(
            reverse("cupping-detail", kwargs={"lot_pk": self.lot.pk, "pk": session.pk})
        ).content.decode()
        crumbs = html[html.index("breadcrumb") :]
        for text in ("Green lots", "XX-24-001", "04 Nov 2026"):
            self.assertIn(text, crumbs)


class LotTests(RoasteryTestCase):
    def test_detail_is_an_accordion_with_the_first_group_open(self):
        self.login()
        html = self.client.get(reverse("lot-detail", kwargs={"pk": self.lot.pk})).content.decode()
        self.assertEqual(html.count('class="accordion-collapse collapse show"'), 1)
        self.assertLess(html.index("Origin and producer"), html.index("Stock and price"))
        self.assertLess(html.index("collapse show"), html.index("Stock and price"))

    def test_lot_delete_previews_sessions(self):
        session = CuppingSession.objects.create(lot=self.lot, held_on=date(2026, 11, 4))
        self.login()
        response = self.client.get(reverse("lot-delete", kwargs={"pk": self.lot.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(session))

    def test_lot_with_batch_is_protected(self):
        batch = RoastBatch.objects.create(
            lot=self.lot,
            roasted_on=date(2026, 11, 4),
            profile="light",
            green_kg=Decimal("12"),
            roasted_kg=Decimal("10.2"),
            roaster=self.users["kim"],
        )
        self.login()
        url = reverse("lot-delete", kwargs={"pk": self.lot.pk})
        response = self.client.get(url)
        self.assertContains(response, str(batch))
        self.assertContains(response, "alert-")
        self.client.post(url)
        self.assertTrue(GreenLot.objects.filter(pk=self.lot.pk).exists())

    def test_lot_pages_render(self):
        self.login()
        for name in ("lot-list", "batch-list", "lot-create", "batch-create"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        lot = GreenLot.objects.exclude(pk=self.lot.pk).first()
        self.assertContains(self.client.get(reverse("lot-detail", kwargs={"pk": lot.pk})), lot.code)
        self.assertContains(self.client.get(reverse("lot-list")), lot.code)

    def test_detail_dates_use_the_project_format(self):
        # config/formats/en: "05 Jan 2026" as on the hand-written pages, not Django's "Jan. 5, 2026"
        self.login()
        html = self.client.get(reverse("lot-detail", kwargs={"pk": self.lot.pk})).content.decode()
        self.assertIn("05 Jan 2026", html)
        self.assertNotIn("Jan. 5, 2026", html)

    def test_kim_can_edit_roastery_sam_cannot(self):
        url = reverse("lot-update", kwargs={"pk": self.lot.pk})
        self.login("kim")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.logout()
        self.login("sam")
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(reverse("lot-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("batch-create")).status_code, 403)


class BatchTests(RoasteryTestCase):
    def test_batch_weight_loss(self):
        batch = RoastBatch(lot=self.lot, green_kg=Decimal("12.0"), roasted_kg=Decimal("10.2"))
        self.assertEqual(batch.weight_loss_pct, Decimal("15.0"))
        self.assertIsNone(RoastBatch(lot=self.lot, green_kg=Decimal("0"), roasted_kg=Decimal("0")).weight_loss_pct)

    def test_batch_create_links_orders(self):
        from sales.models import Order

        order = (
            Order.objects.filter(state=OrderState.CONFIRMED).first()
            or Order.objects.filter(state=OrderState.ROASTED).first()
        )
        self.login("kim")
        data = {
            "lot": str(self.lot.pk),
            "roasted_on": "2026-11-04",
            "profile": "light",
            "green_kg": "12.0",
            "roasted_kg": "10.2",
            "roaster": str(self.users["kim"].pk),
            "orders": [str(order.pk)],
        }
        response = self.client.post(reverse("batch-create"), data)
        self.assertEqual(response.status_code, 302)
        batch = RoastBatch.objects.get(lot=self.lot)
        self.assertEqual(list(batch.orders.all()), [order])
        # a draft order is not selectable
        draft = Order.objects.filter(state=OrderState.DRAFT).first()
        if draft:
            self.assertEqual(
                self.client.post(reverse("batch-create"), {**data, "orders": [str(draft.pk)]}).status_code, 200
            )

    def test_roasted_kg_cannot_exceed_green(self):
        self.login("kim")
        data = {
            "lot": str(self.lot.pk),
            "roasted_on": "2026-11-04",
            "profile": "light",
            "green_kg": "10",
            "roasted_kg": "11",
            "roaster": str(self.users["kim"].pk),
        }
        self.assertEqual(self.client.post(reverse("batch-create"), data).status_code, 200)
        self.assertFalse(RoastBatch.objects.exists() and RoastBatch.objects.filter(lot=self.lot).exists())


class BatchStockTests(RoasteryTestCase):
    """A roast batch draws its green weight from the lot's ``kg_on_hand``."""

    def data(self, **extra):
        return {
            "lot": str(self.lot.pk),
            "roasted_on": "2026-11-04",
            "profile": "light",
            "green_kg": "12.0",
            "roasted_kg": "10.2",
            "roaster": str(self.users["kim"].pk),
            **extra,
        }

    def on_hand(self, lot=None):
        return GreenLot.objects.get(pk=(lot or self.lot).pk).kg_on_hand

    def make(self, green="12.0", lot=None):
        lot = lot or self.lot
        self.login("kim")
        before = RoastBatch.objects.count()
        response = self.client.post(reverse("batch-create"), self.data(lot=str(lot.pk), green_kg=green))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoastBatch.objects.count(), before + 1)
        return RoastBatch.objects.latest("pk")

    def test_create_decrements_the_lot(self):
        self.make("12.0")
        self.assertEqual(self.on_hand(), Decimal("588.0"))

    def test_create_beyond_stock_is_refused(self):
        self.login("kim")
        response = self.client.post(reverse("batch-create"), self.data(green_kg="600.1", roasted_kg="500"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("green_kg", response.context["form"].errors)
        self.assertEqual(self.on_hand(), Decimal("600"))
        self.assertFalse(RoastBatch.objects.filter(lot=self.lot).exists())

    def test_update_adjusts_by_the_difference(self):
        batch = self.make("12.0")
        url = reverse("batch-update", kwargs={"pk": batch.pk})
        response = self.client.post(url, self.data(green_kg="20.0", roasted_kg="17"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.on_hand(), Decimal("580.0"))
        response = self.client.post(url, self.data(green_kg="5.0", roasted_kg="4"))
        self.assertEqual(self.on_hand(), Decimal("595.0"))
        # the whole lot may be used by this batch: its own weight counts as available again
        self.assertEqual(self.client.post(url, self.data(green_kg="600.0", roasted_kg="500")).status_code, 302)
        self.assertEqual(self.on_hand(), Decimal("0.0"))

    def test_update_moving_to_another_lot(self):
        batch = self.make("12.0")
        other = GreenLot.objects.exclude(pk=self.lot.pk).filter(kg_on_hand__gte=50).first()
        before = self.on_hand(other)
        response = self.client.post(
            reverse("batch-update", kwargs={"pk": batch.pk}),
            self.data(lot=str(other.pk), green_kg="10.0", roasted_kg="8"),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.on_hand(), Decimal("600"))
        self.assertEqual(self.on_hand(other), before - Decimal("10.0"))

    def test_delete_restores_the_stock(self):
        batch = self.make("12.0")
        self.assertEqual(
            self.client.post(reverse("batch-delete", kwargs={"pk": batch.pk}), {"confirm": "on"}).status_code, 302
        )
        self.assertFalse(RoastBatch.objects.filter(pk=batch.pk).exists())
        self.assertEqual(self.on_hand(), Decimal("600.0"))

    def test_seed_leaves_every_lot_with_sensible_stock(self):
        for lot in GreenLot.objects.exclude(pk=self.lot.pk):
            self.assertGreaterEqual(lot.kg_on_hand, 0, lot)
            self.assertLessEqual(lot.kg_on_hand, lot.kg_purchased, lot)
