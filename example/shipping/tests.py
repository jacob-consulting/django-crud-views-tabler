import random

from catalog.seed import seed as seed_catalog
from dashboard.seed import seed as seed_dashboard
from django.test import TestCase
from django.urls import reverse
from sales.models import Order, OrderState
from sales.seed import seed as seed_sales

from .courier import carrier_for, fetch_shipments, tracking_number


class ShippingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.world = {}
        rng = random.Random(1)
        seed_dashboard(rng, cls.world)
        seed_catalog(rng, cls.world)
        seed_sales(rng, cls.world)
        cls.shipped = Order.objects.filter(state__in=[OrderState.SHIPPED, OrderState.DELIVERED]).select_related(
            "customer"
        )
        cls.sam = cls.world["users"]["sam"]

    def login(self, username="alex"):
        self.client.login(username=username, password="demo")


class CourierTests(ShippingTestCase):
    def test_payload_is_deterministic(self):
        self.assertEqual(fetch_shipments(), fetch_shipments())

    def test_payload_shape(self):
        order = self.shipped.first()
        row = next(r for r in fetch_shipments() if r["order_number"] == order.number)
        self.assertEqual(row["tracking_number"], f"ACME{order.number:08d}")
        self.assertEqual(row["tracking_number"], tracking_number(order.number))
        self.assertEqual(row["carrier"], carrier_for(order.number))
        self.assertIn(row["status"], ("in_transit", "delivered"))
        self.assertEqual(row["status"], "delivered" if order.state == OrderState.DELIVERED else "in_transit")
        self.assertTrue(3 <= len(row["events"]) <= 5)


class ShipmentViewTests(ShippingTestCase):
    def test_list_shows_one_row_per_shipped_order(self):
        self.login()
        response = self.client.get(reverse("shipment-list"), {"per_page": 100})
        self.assertEqual(response.status_code, 200)
        shown = [s.order_number for s in response.context["table"].data]
        self.assertEqual(sorted(shown), sorted(self.shipped.values_list("number", flat=True)))
        self.assertTrue(shown)

    def test_detail_lists_events(self):
        self.login()
        order = self.shipped.first()
        response = self.client.get(reverse("shipment-detail", kwargs={"pk": tracking_number(order.number)}))
        self.assertEqual(response.status_code, 200)
        row = next(r for r in fetch_shipments() if r["order_number"] == order.number)
        for event in row["events"]:
            self.assertContains(response, event["description"])
        self.assertContains(response, "timeline-event")

    def test_unknown_tracking_number_404(self):
        self.login()
        response = self.client.get(reverse("shipment-detail", kwargs={"pk": "ACME99999999"}))
        self.assertEqual(response.status_code, 404)

    def test_sam_sees_only_shipments_of_granted_customers(self):
        granted = set(self.shipped.filter(customer__owner=self.sam).values_list("number", flat=True))
        others = self.shipped.exclude(customer__owner=self.sam)
        self.assertTrue(granted and others.exists())
        self.login("sam")
        response = self.client.get(reverse("shipment-list"), {"per_page": 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual({s.order_number for s in response.context["table"].data}, granted)

    def test_sam_gets_404_for_a_shipment_of_another_rep(self):
        self.login("sam")
        foreign = self.shipped.exclude(customer__owner=self.sam).first()
        response = self.client.get(reverse("shipment-detail", kwargs={"pk": tracking_number(foreign.number)}))
        self.assertEqual(response.status_code, 404)
        mine = self.shipped.filter(customer__owner=self.sam).first()
        response = self.client.get(reverse("shipment-detail", kwargs={"pk": tracking_number(mine.number)}))
        self.assertEqual(response.status_code, 200)

    def test_kim_sees_all_and_anonymous_is_redirected(self):
        self.login("kim")
        response = self.client.get(reverse("shipment-list"), {"per_page": 100})
        self.assertEqual(len(response.context["table"].data), self.shipped.count())
        self.client.logout()
        self.assertEqual(self.client.get(reverse("shipment-list")).status_code, 302)

    def test_order_detail_links_to_shipment_only_when_shipped(self):
        self.login()
        order = self.shipped.first()
        url = reverse("order-detail", kwargs={"customer_pk": order.customer_id, "pk": order.pk})
        self.assertContains(
            self.client.get(url), reverse("shipment-detail", kwargs={"pk": tracking_number(order.number)})
        )
        open_order = Order.objects.exclude(state__in=[OrderState.SHIPPED, OrderState.DELIVERED]).first()
        url = reverse("order-detail", kwargs={"customer_pk": open_order.customer_id, "pk": open_order.pk})
        self.assertNotContains(self.client.get(url), "Track shipment")
