import random
from html import escape

from catalog.seed import seed as seed_catalog
from dashboard.seed import seed as seed_dashboard
from django.test import TestCase
from django.urls import reverse

from sales.models import Address, Customer
from sales.seed import seed as seed_sales

CONSUMER_POST = {"name": "Test Person", "kind": "consumer", "country": "DE", "city": "Bonn"}
WHOLESALE_FIELDS = {"company": "Acme GmbH", "vat_id": "DE123", "price_tier": "A", "payment_terms": "net_30"}


class SalesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.world = {}
        rng = random.Random(1)
        seed_dashboard(rng, cls.world)
        seed_catalog(rng, cls.world)  # the seeded orders need products
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
        self.assertEqual(
            [str(Customer(kind="wholesale", price_tier=t).discount) for t in "ABC"], ["0.20", "0.12", "0.05"]
        )
        self.assertEqual(Customer(kind="consumer").discount, 0)


class CustomerFormTests(SalesTestCase):
    def test_wholesale_group_is_conditional(self):
        self.login()
        html = self.client.get(reverse("customer-create")).content.decode()
        group = html[html.index("cv-data-toggle-group") :]
        for field in ("company", "vat_id", "price_tier", "payment_terms"):
            self.assertIn(f'name="{field}"', group)
        self.assertIn('cv-data-toggle-field="kind"', html)
        self.assertIn('cv-data-toggle-values="[&quot;wholesale&quot;]"', html)
        self.assertIn('<select name="kind"', html)
        self.assertNotIn('name="is_wholesale"', html)
        self.assertIn('<option value="consumer" selected>Consumer</option>', html)
        self.assertIn('<legend class="cv-tabler-section-legend">Wholesale terms</legend>', html)

        # a consumer with the wholesale fields filled saves them empty
        response = self.client.post(reverse("customer-create"), {**CONSUMER_POST, **WHOLESALE_FIELDS})
        self.assertEqual(response.status_code, 302)
        customer = Customer.objects.get(name="Test Person")
        self.assertEqual(customer.kind, "consumer")
        self.assertEqual(
            (customer.company, customer.vat_id, customer.price_tier, customer.payment_terms), ("", "", None, None)
        )

        # wholesale without a company is refused
        response = self.client.post(
            reverse("customer-create"),
            {**CONSUMER_POST, **WHOLESALE_FIELDS, "name": "Shop", "kind": "wholesale", "company": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("company", response.context["form"].errors)
        self.assertFalse(Customer.objects.filter(name="Shop").exists())

        response = self.client.post(
            reverse("customer-create"), {**CONSUMER_POST, **WHOLESALE_FIELDS, "name": "Shop", "kind": "wholesale"}
        )
        self.assertEqual(response.status_code, 302)
        shop = Customer.objects.get(name="Shop")
        self.assertEqual((shop.kind, shop.price_tier), ("wholesale", "A"))

    def test_edit_form_starts_with_the_stored_kind(self):
        self.login()
        for kind, label in Customer.Kind.choices:
            with self.subTest(kind=kind):
                customer = Customer.objects.filter(kind=kind).first()
                html = self.client.get(reverse("customer-update", kwargs={"pk": customer.pk})).content.decode()
                self.assertIn(f'<option value="{kind}" selected>{label}</option>', html)

    def test_switching_to_consumer_clears_wholesale_terms(self):
        self.login()
        customer = Customer.objects.filter(kind="wholesale").first()
        response = self.client.post(
            reverse("customer-update", kwargs={"pk": customer.pk}),
            {**CONSUMER_POST, **WHOLESALE_FIELDS, "price_tier": "invalid", "payment_terms": "invalid"},
        )
        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertEqual(customer.kind, "consumer")
        self.assertEqual(
            (customer.company, customer.vat_id, customer.price_tier, customer.payment_terms), ("", "", None, None)
        )

    def test_switching_to_wholesale_saves_terms(self):
        self.login()
        customer = Customer.objects.filter(kind="consumer").first()
        response = self.client.post(
            reverse("customer-update", kwargs={"pk": customer.pk}),
            {**CONSUMER_POST, **WHOLESALE_FIELDS, "kind": "wholesale"},
        )
        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertEqual(customer.kind, "wholesale")
        self.assertEqual(
            (customer.company, customer.vat_id, customer.price_tier, customer.payment_terms),
            ("Acme GmbH", "DE123", "A", "net_30"),
        )

    def test_wholesale_requires_all_terms_except_vat_id(self):
        self.login()
        for field in ("company", "price_tier", "payment_terms"):
            with self.subTest(field=field):
                response = self.client.post(
                    reverse("customer-create"),
                    {**CONSUMER_POST, **WHOLESALE_FIELDS, "kind": "wholesale", field: ""},
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
        response = self.client.post(
            reverse("customer-create"),
            {**CONSUMER_POST, **WHOLESALE_FIELDS, "kind": "wholesale", "vat_id": ""},
        )
        self.assertEqual(response.status_code, 302)

    def test_missing_or_invalid_kind_does_not_update_customer(self):
        self.login()
        customer = Customer.objects.filter(kind="wholesale").first()
        original = (customer.kind, customer.company, customer.vat_id, customer.price_tier, customer.payment_terms)
        for kind in ("", "invalid"):
            with self.subTest(kind=kind):
                response = self.client.post(
                    reverse("customer-update", kwargs={"pk": customer.pk}),
                    {**CONSUMER_POST, "kind": kind},
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("kind", response.context["form"].errors)
                customer.refresh_from_db()
                self.assertEqual(
                    (customer.kind, customer.company, customer.vat_id, customer.price_tier, customer.payment_terms),
                    original,
                )

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
        self.assertIn(reverse("order-list", kwargs={"customer_pk": customer.pk}), html)  # the Orders link
        self.assertIn(reverse("subscription-list", kwargs={"customer_pk": customer.pk}), html)  # the Subscriptions link

    def test_detail_shows_a_dash_for_blank_optional_rows(self):
        self.login()
        customer = Customer.objects.filter(kind="consumer").first()
        Customer.objects.filter(pk=customer.pk).update(phone="", notes="")
        html = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).content.decode()
        for label in ("Phone", "Notes"):
            # the dash sits in the value cell right after the label, not in some later row
            self.assertRegex(
                html, rf">\s*{label}\s*</div>\s*<div[^>]*>\s*<span class=\"text-body-tertiary\">&mdash;</span>"
            )
        Customer.objects.filter(pk=customer.pk).update(phone="+49 40 123", notes="Likes it light")
        html = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).content.decode()
        self.assertRegex(html, r">\s*Phone\s*<")
        self.assertIn("Likes it light", html)

    def test_detail_shows_choice_labels_and_no_model_help_text(self):
        self.login()
        customer = Customer.objects.filter(kind="wholesale").first()
        Customer.objects.filter(pk=customer.pk).update(payment_terms=Customer.PaymentTerms.NET_60, country="DE")
        html = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).content.decode()
        self.assertRegex(html, r">\s*Payment terms\s*<")
        self.assertRegex(html, r">\s*Net 60\s*<")
        self.assertNotRegex(html, r">\s*net_60\s*<")
        self.assertNotIn("ISO country code", html)  # the model help text is for the form only
        form = self.client.get(reverse("customer-update", kwargs={"pk": customer.pk})).content.decode()
        self.assertIn("ISO country code, e.g. DE.", form)

    def test_detail_view_title_is_details(self):
        # the customer's name is the page's h1 (ViewSet Navigation); the detail view is titled like its tab, so the
        # theme leaves the heading out and keeps the subline
        self.login()
        customer = Customer.objects.first()
        html = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).content.decode()
        page = html[html.index('class="page-header') : html.index('class="page-body')]
        self.assertNotIn("<h2", page)
        self.assertIn("page-subtitle", page)
        self.assertIn(f"<title>Details · {customer.name}", html.replace("&amp;", "&").replace("&#x27;", "'"))

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
        customer = Customer.objects.filter(kind="consumer", orders__isnull=True).first()  # orders protect a customer
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
        self.assertIn(
            self.client.get(reverse("address-list", kwargs={"customer_pk": self.other.pk})).status_code, (403, 404)
        )
        self.assertIn(
            self.client.get(
                reverse("address-detail", kwargs={"customer_pk": self.other.pk, "pk": address.pk})
            ).status_code,
            (403, 404),
        )
        self.assertIn(
            self.client.post(reverse("address-create", kwargs={"customer_pk": self.other.pk}), {}).status_code,
            (403, 404),
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
        self.assertEqual(self.client.get(reverse("address-list", kwargs={"customer_pk": customer.pk})).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("address-create", kwargs={"customer_pk": customer.pk})).status_code, 403
        )


class AddressTests(SalesTestCase):
    def test_mark_default_address(self):
        self.login()
        customer = Customer.objects.filter(kind="wholesale").first()
        previous = customer.addresses.get(is_default=True)
        second = Address.objects.create(
            customer=customer, label="Depot", street="X 1", zip_code="1", city="Y", country="DE"
        )
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

    def test_sam_cannot_change_addresses_of_other_customers(self):
        self.login("sam")
        address = self.other.addresses.first()
        kwargs = {"customer_pk": self.other.pk, "pk": address.pk}
        data = {"label": "Hijacked", "street": "X 1", "zip_code": "1", "city": "Y", "country": "DE"}
        self.assertEqual(self.client.post(reverse("address-update", kwargs=kwargs), data).status_code, 403)
        self.assertEqual(self.client.post(reverse("address-delete", kwargs=kwargs), {"confirm": "on"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("address-make_default", kwargs=kwargs)).status_code, 403)
        address.refresh_from_db()
        self.assertNotEqual(address.label, "Hijacked")

        # cross-parent: Sam's own customer in the URL, another customer's address
        cross = {"customer_pk": self.granted.first().pk, "pk": address.pk}
        for name in ("address-detail", "address-update", "address-delete"):
            self.assertEqual(self.client.get(reverse(name, kwargs=cross)).status_code, 404, name)
        self.assertEqual(self.client.post(reverse("address-make_default", kwargs=cross)).status_code, 404)
        self.assertEqual(self.client.post(reverse("address-update", kwargs=cross), data).status_code, 404)
        address.refresh_from_db()
        self.assertNotEqual(address.label, "Hijacked")


class OwnerGrantTests(SalesTestCase):
    def update_post(self, customer, owner):
        data = {
            "name": customer.name,
            "kind": customer.kind,
            "country": customer.country or "DE",
            "city": customer.city,
            "owner": str(owner.pk) if owner else "",
        }
        if customer.is_wholesale:
            data.update(company=customer.company, price_tier=customer.price_tier, payment_terms=customer.payment_terms)
        return self.client.post(reverse("customer-update", kwargs={"pk": customer.pk}), data)

    def test_assigning_an_account_manager_grants_access(self):
        customer = Customer.objects.exclude(owner=self.sam).filter(kind="consumer").first()
        self.assertEqual(self.client.login(username="sam", password="demo"), True)
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).status_code, 403)
        self.login()
        self.assertEqual(self.update_post(customer, self.sam).status_code, 302)
        self.login("sam")
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk})).status_code, 200)
        self.assertIn(customer.pk, {c.pk for c in self.client.get(reverse("customer-list")).context["table"].data.data})

    def test_new_owner_sees_the_orders(self):
        customer = Customer.objects.exclude(owner=self.sam).filter(orders__isnull=False).first()
        self.login()
        self.assertEqual(self.update_post(customer, self.sam).status_code, 302)
        self.login("sam")
        self.assertEqual(self.client.get(reverse("order-list", kwargs={"customer_pk": customer.pk})).status_code, 200)
        table = self.client.get(reverse("orders-list"), {"per_page": 100}).context["table"]
        self.assertIn(customer.pk, {o.customer_id for o in table.data})

    def test_reassigning_withdraws_the_previous_owners_access(self):
        mine = self.granted.first()
        self.login()
        self.assertEqual(self.update_post(mine, self.world["users"]["alex"]).status_code, 302)
        self.login("sam")
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": mine.pk})).status_code, 403)
        self.assertEqual(self.client.get(reverse("order-list", kwargs={"customer_pk": mine.pk})).status_code, 403)
        # alex keeps working through his model-level permissions, other grants of Sam stay
        self.login()
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": mine.pk})).status_code, 200)
        other_mine = self.granted.exclude(pk=mine.pk).first()
        self.login("sam")
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": other_mine.pk})).status_code, 200)

    def test_unchanged_owner_keeps_the_grant_and_creator_grant_survives(self):
        mine = self.granted.first()
        self.login()
        self.assertEqual(self.update_post(mine, self.sam).status_code, 302)
        self.login("sam")
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": mine.pk})).status_code, 200)

    def test_alex_creating_for_sam_grants_sam(self):
        self.login()
        response = self.client.post(
            reverse("customer-create"), {**CONSUMER_POST, "name": "For Sam", "owner": str(self.sam.pk)}
        )
        self.assertEqual(response.status_code, 302)
        created = Customer.objects.get(name="For Sam")
        self.login("sam")
        self.assertEqual(self.client.get(reverse("customer-detail", kwargs={"pk": created.pk})).status_code, 200)


class FilterScopeTests(SalesTestCase):
    def test_filter_choices_are_limited_to_visible_customers(self):
        foreign = Customer.objects.exclude(owner=self.sam).exclude(owner=None).first()
        Customer.objects.filter(pk=foreign.pk).update(country="ZZ")
        self.login("sam")
        form = self.client.get(reverse("customer-list")).context["filter"].form
        countries = [value for value, _ in form.fields["country"].choices]
        self.assertNotIn("ZZ", countries)
        self.assertEqual(set(countries) - {""}, set(self.granted.values_list("country", flat=True)) - {""})
        owners = list(form.fields["owner"].queryset)
        self.assertEqual(owners, [self.sam])
        self.login()
        form = self.client.get(reverse("customer-list")).context["filter"].form
        self.assertIn("ZZ", [value for value, _ in form.fields["country"].choices])
