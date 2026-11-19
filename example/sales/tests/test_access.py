"""Who reaches which nested page of a customer: the access matrix for Sam (object grants), Kim and Alex."""

from django.urls import reverse

from sales.models import Address, CustomerSubscription, Order, OrderState

from .test_orders import OrderTestCase, history
from .test_subscriptions import TODAY

# (url name, kwargs from the fixtures of one customer, HTTP method)
LIST_PAGES = (
    ("address-list", "customer", "get"),
    ("order-list", "customer", "get"),
    ("subscription-list", "customer", "get"),
)
CREATE_PAGES = (
    ("address-create", "customer", "get"),
    ("order-create", "customer", "get"),
    ("subscription-create", "customer", "get"),
)
ITEM_PAGES = (
    ("address-detail", "address", "get"),
    ("address-update", "address", "get"),
    ("address-delete", "address", "get"),
    ("address-make_default", "address", "get"),
    ("order-detail", "order", "get"),
    ("order-update", "order", "get"),
    ("order-delete", "order", "get"),
    ("order-packing_slip", "order", "get"),
    ("order-duplicate", "order", "get"),
    ("order-workflow", "order", "get"),
    ("subscription-update", "subscription", "get"),
    ("subscription-delete", "subscription", "get"),
)
WRITES = (
    ("address-create", "customer", "post"),
    ("address-update", "address", "post"),
    ("address-delete", "address", "post"),
    ("address-make_default", "address", "post"),
    ("order-create", "customer", "post"),
    ("order-update", "order", "post"),
    ("order-delete", "order", "post"),
    ("order-duplicate", "order", "post"),
    ("order-workflow", "order", "post"),
    ("subscription-create", "customer", "post"),
    ("subscription-update", "subscription", "post"),
    ("subscription-delete", "subscription", "post"),
)


class AccessMatrixTests(OrderTestCase):
    def build(self, customer):
        """The kwargs of every endpoint kind for one customer, with a fresh address, order and subscription."""
        address = Address.objects.create(
            customer=customer, label="Spare", street="1 Main St", zip_code="10115", city="Berlin", country="DE"
        )
        order = self.make_order(customer=customer)
        sub = CustomerSubscription.objects.create(
            customer=customer, product=self.weekly, started_on=TODAY, next_delivery=TODAY, is_active=True
        )
        return {
            "customer": {"customer_pk": customer.pk},
            "address": {"customer_pk": customer.pk, "pk": address.pk},
            "order": {"customer_pk": customer.pk, "pk": order.pk},
            "subscription": {"customer_pk": customer.pk, "pk": sub.pk},
        }, order

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from catalog.models import Subscription

        cls.weekly = Subscription.objects.first()

    def request(self, endpoint, fixtures):
        name, kind, method = endpoint
        return getattr(self.client, method)(reverse(name, kwargs=fixtures[kind]), {})

    def snapshot(self):
        return (
            Address.objects.count(),
            Order.objects.count(),
            CustomerSubscription.objects.count(),
            sorted(Address.objects.values_list("pk", "is_default")),
            sorted(Order.objects.values_list("pk", "state")),
        )

    def test_sam_is_refused_on_other_customers_nested_pages(self):
        fixtures, _order = self.build(self.other)
        before = self.snapshot()
        self.login("sam")
        for endpoint in LIST_PAGES + CREATE_PAGES + ITEM_PAGES + WRITES:
            response = self.request(endpoint, fixtures)
            self.assertEqual(response.status_code, 403, msg=f"{endpoint[2].upper()} {endpoint[0]}")
        self.assertEqual(self.snapshot(), before)

    def test_sam_reaches_his_customers_nested_pages(self):
        fixtures, order = self.build(self.mine)
        self.login("sam")
        for name, kind, method in LIST_PAGES + ITEM_PAGES:
            if name.endswith(("-delete", "-make_default")) or name in ("order-update", "order-duplicate"):
                continue  # changing pages are covered below and by the role tests
            response = self.request((name, kind, method), fixtures)
            self.assertEqual(response.status_code, 200, msg=name)
        self.assertEqual(
            self.request(("address-update", "address", "get"), fixtures).status_code, 200, msg="address-update"
        )
        response = self.client.post(reverse("address-make_default", kwargs=fixtures["address"]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Address.objects.get(pk=fixtures["address"]["pk"]).is_default)
        response = self.client.post(reverse("order-workflow", kwargs=fixtures["order"]), {"transition": "wf_confirm"})
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.CONFIRMED)

    def test_kim_reads_every_customers_nested_lists(self):
        self.login("kim")
        for customer in (self.mine, self.other):
            for name in ("address-list", "order-list", "subscription-list"):
                response = self.client.get(reverse(name, kwargs={"customer_pk": customer.pk}))
                self.assertEqual(response.status_code, 200, msg=f"{name} {customer.pk}")

    def test_kim_cannot_write_addresses_or_subscriptions(self):
        fixtures, _order = self.build(self.other)
        self.login("kim")
        for endpoint in (
            ("address-create", "customer", "get"),
            ("address-update", "address", "get"),
            ("address-make_default", "address", "get"),
            ("subscription-create", "customer", "get"),
        ):
            self.assertEqual(self.request(endpoint, fixtures).status_code, 403, msg=endpoint[0])

    def test_kim_roasts_any_customers_order(self):
        order = self.make_order(customer=self.other, state=OrderState.CONFIRMED)
        self.login("kim")
        response = self.client.post(
            reverse("order-workflow", kwargs=self.order_kwargs(order)), {"transition": "wf_roast"}
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.ROASTED)
        self.assertTrue(history(order).exists())

    def test_alex_reaches_everything(self):
        fixtures, _order = self.build(self.other)
        self.login("alex")
        for endpoint in LIST_PAGES + CREATE_PAGES + ITEM_PAGES:
            if endpoint[0] == "address-make_default":
                continue  # an action view: POST only, below
            self.assertEqual(self.request(endpoint, fixtures).status_code, 200, msg=endpoint[0])
        response = self.client.post(reverse("address-make_default", kwargs=fixtures["address"]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Address.objects.get(pk=fixtures["address"]["pk"]).is_default)
