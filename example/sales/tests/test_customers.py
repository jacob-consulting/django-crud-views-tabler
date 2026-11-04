import random
from html import escape

from django.test import TestCase
from django.urls import reverse

from dashboard.seed import seed as seed_dashboard
from sales.models import Address, Customer
from sales.permissions import grant_customer
from sales.seed import seed as seed_sales

CONSUMER_POST = {"name": "Test Person", "country": "DE", "city": "Bonn"}
WHOLESALE_FIELDS = {"company": "Acme GmbH", "vat_id": "DE123", "price_tier": "A", "payment_terms": "net_30"}


class SalesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.world = {}
        rng = random.Random(1)
        seed_dashboard(rng, cls.world)
        seed_sales(rng, cls.world)
        cls.sam = cls.world["users"]["sam"]
        cls.granted = Customer.objects.filter(owner=cls.sam)
        cls.other = Customer.objects.exclude(owner=cls.sam).filter(kind="wholesale").first()

    def login(self, username="alex"):
        self.client.login(username=username, password="demo")


class SeedTests(SalesTestCase):
    def test_seed_shape(self):
        self.assertGreaterEqual(len(self.world["customers"]), 20)
        self.assertGreaterEqual(self.granted.count(), 3)
        self.assertTrue(Customer.objects.filter(kind="consumer").exists())
        for customer in Customer.objects.all():
            self.assertEqual(customer.addresses.filter(is_default=True).count(), 1)

    def test_discount(self):
        self.assertEqual([str(Customer(kind="wholesale", price_tier=t).discount) for t in "ABC"], ["0.20", "0.12", "0.05"])
        self.assertEqual(Customer(kind="consumer").discount, 0)


class CustomerFormTests(SalesTestCase):
    def test_wholesale_group_is_conditional(self):
        self.login()
        html = self.client.get(reverse("customer-create")).content.decode()
        group = html[html.index("cv-data-toggle-group") :]
        for field in ("company", "vat_id", "price_tier", "payment_terms"):
            self.assertIn(f'name="{field}"', group)
        self.assertIn('cv-data-toggle-field="is_wholesale"', html)

        # a consumer with the wholesale fields filled saves them empty
        response = self.client.post(reverse("customer-create"), {**CONSUMER_POST, **WHOLESALE_FIELDS})
        self.assertEqual(response.status_code, 302)
        customer = Customer.objects.get(name="Test Person")
        self.assertEqual(customer.kind, "consumer")
        self.assertEqual((customer.company, customer.vat_id, customer.price_tier, customer.payment_terms), ("", "", None, None))

        # wholesale without a company is refused
        response = self.client.post(
            reverse("customer-create"),
            {**CONSUMER_POST, **WHOLESALE_FIELDS, "name": "Shop", "is_wholesale": "on", "company": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("company", response.context["form"].errors)
        self.assertFalse(Customer.objects.filter(name="Shop").exists())

        response = self.client.post(
            reverse("customer-create"), {**CONSUMER_POST, **WHOLESALE_FIELDS, "name": "Shop", "is_wholesale": "on"}
        )
        self.assertEqual(response.status_code, 302)
        shop = Customer.objects.get(name="Shop")
        self.assertEqual((shop.kind, shop.price_tier), ("wholesale", "A"))

    def test_edit_form_starts_with_the_stored_kind(self):
        self.login()
        wholesale = Customer.objects.filter(kind="wholesale").first()
        html = self.client.get(reverse("customer-update", kwargs={"pk": wholesale.pk})).content.decode()
        self.assertRegex(html, r'name="is_wholesale"[^>]*checked|checked[^>]*name="is_wholesale"')

    def test_creator_gets_a_grant(self):
        self.login("sam")
        response = self.client.post(reverse("customer-create"), {**CONSUMER_POST, "name": "Sams new one"})
        self.assertEqual(response.status_code, 302)
        created = Customer.objects.get(name="Sams new one")
        self.assertEqual(created.owner, self.sam)
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": created.pk})).status_code, 200)


class CustomerViewTests(SalesTestCase):
    def test_detail_property_grid(self):
        self.login()
        customer = Customer.objects.filter(kind="wholesale").first()
        html = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).content.decode()
        self.assertIn("Price tier", html)
        self.assertIn(customer.get_price_tier_display(), html)
        self.assertIn(reverse("address-list", kwargs={"customer_pk": customer.pk}), html)  # the Addresses link
        self.assertIn("Wholesale", html)
        # TODO(Task 6/7): assert the Orders and Subscriptions links once those child views exist

    def test_consumer_detail_has_no_wholesale_terms(self):
        self.login()
        consumer = Customer.objects.filter(kind="consumer").first()
        html = self.client.get(reverse("customer-detail", kwargs={"pk": consumer.pk})).content.decode()
        self.assertNotIn("Price tier", html)

    def test_list_filters(self):
        self.login()
        html = self.client.get(reverse("customer-list"), {"kind": "consumer"}).content.decode()
        self.assertIn(Customer.objects.filter(kind="consumer").first().name, html)
        self.assertNotIn(Customer.objects.filter(kind="wholesale").first().name, html)

    def test_delete_cascades_addresses(self):
        self.login()
        customer = Customer.objects.filter(kind="consumer").first()
        url = reverse("customer-delete", kwargs={"pk": customer.pk})
        self.assertContains(self.client.get(url), customer.name)
        self.assertEqual(self.client.post(url, {"confirm": "on"}).status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())
        self.assertFalse(Address.objects.filter(customer_id=customer.pk).exists())


class RoleTests(SalesTestCase):
    def test_sam_sees_only_granted_customers(self):
        self.login("sam")
        response = self.client.get(reverse("customer-list"), {"page": 1})
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for customer in self.granted:
            self.assertIn(escape(customer.name), html)
        shown = {c.pk for c in Customer.objects.all() if escape(c.name) in html}
        self.assertEqual(shown, set(self.granted.values_list("pk", flat=True)))

        for url_name in ("customer-detail", "customer-update", "customer-delete"):
            status = self.client.get(reverse(url_name, kwargs={"pk": self.other.pk})).status_code
            self.assertIn(status, (403, 404), url_name)
        address = self.other.addresses.first()
        self.assertIn(self.client.get(reverse("address-list", kwargs={"customer_pk": self.other.pk})).status_code, (403, 404))
        self.assertIn(
            self.client.get(reverse("address-detail", kwargs={"customer_pk": self.other.pk, "pk": address.pk})).status_code,
            (403, 404),
        )
        self.assertIn(
            self.client.post(reverse("address-create", kwargs={"customer_pk": self.other.pk}), {}).status_code, (403, 404)
        )
        # ... but the granted customer's pages open
        mine = self.granted.first()
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": mine.pk})).status_code, 200)
        self.assertEqual(self.client.get(reverse("address-list", kwargs={"customer_pk": mine.pk})).status_code, 200)

    def test_sam_has_no_model_level_view_permission(self):
        self.assertFalse(self.sam.has_perm("sales.view_customer"))
        self.login("sam")
        self.assertContains(self.client.get(reverse("dashboard:index")), reverse("customer-list"))  # the nav entry

    def test_sam_cannot_delete_a_granted_customer(self):
        self.login("sam")
        status = self.client.get(reverse("customer-delete", kwargs={"pk": self.granted.first().pk})).status_code
        self.assertEqual(status, 403)  # granted view and change only

    def test_kim_views_but_does_not_edit(self):
        self.login("kim")
        customer = Customer.objects.first()
        self.assertEqual(self.client.get(reverse("customer-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).status_code, 200)
        self.assertEqual(self.client.get(reverse("customer-update", kwargs={"pk": customer.pk})).status_code, 403)
        self.assertEqual(self.client.get(reverse("customer-create")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("address-list", kwargs={"customer_pk": customer.pk})).status_code, 200
        )
        self.assertEqual(
            self.client.get(reverse("address-create", kwargs={"customer_pk": customer.pk})).status_code, 403
        )


class AddressTests(SalesTestCase):
    def test_mark_default_address(self):
        self.login()
        customer = Customer.objects.filter(kind="wholesale").first()
        previous = customer.addresses.get(is_default=True)
        second = Address.objects.create(customer=customer, label="Depot", street="X 1", zip_code="1", city="Y", country="DE")
        url = reverse("address-make_default", kwargs={"customer_pk": customer.pk, "pk": second.pk})
        self.assertEqual(self.client.post(url).status_code, 302)
        second.refresh_from_db()
        previous.refresh_from_db()
        self.assertTrue(second.is_default)
        self.assertFalse(previous.is_default)

    def test_create_address_under_the_customer(self):
        self.login()
        customer = Customer.objects.first()
        url = reverse("address-create", kwargs={"customer_pk": customer.pk})
        data = {"label": "Depot", "street": "Hafenweg 3", "zip_code": "20457", "city": "Hamburg", "country": "DE"}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(Address.objects.get(label="Depot").customer, customer)

    def test_sam_manages_granted_customers_addresses(self):
        self.login("sam")
        customer = self.granted.first()
        address = customer.addresses.first()
        data = {"label": "Changed", "street": "Hafenweg 3", "zip_code": "20457", "city": "Hamburg", "country": "DE"}
        url = reverse("address-update", kwargs={"customer_pk": customer.pk, "pk": address.pk})
        self.assertEqual(self.client.post(url, data).status_code, 302)
        address.refresh_from_db()
        self.assertEqual(address.label, "Changed")
