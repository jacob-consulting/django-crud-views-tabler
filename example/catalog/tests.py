import random
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from dashboard.seed import seed as seed_dashboard
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Beans, Category, Equipment, Product, Subscription
from .seed import seed as seed_catalog
from .views import PROPERTY_DISPLAY, ProductDetailView


class CatalogTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.world = {}
        rng = random.Random(1)
        seed_dashboard(rng, cls.world)
        seed_catalog(rng, cls.world)

    def login(self, username="alex"):
        self.client.login(username=username, password="demo")

    def ctype_id(self, model):
        return ContentType.objects.get_for_model(model).pk


class SeedTests(CatalogTestCase):
    def test_seed_covers_every_kind(self):
        for model in (Beans, Equipment, Subscription):
            self.assertTrue(model.objects.exists(), model)
        self.assertEqual(len(self.world["products"]), Product.objects.count())
        self.assertTrue(Product.objects.get(pk=Beans.objects.first().pk).is_beans)
        self.assertFalse(Equipment.objects.first().is_beans)


class ProductViewTests(CatalogTestCase):
    def test_declared_mapping_tracer(self):
        self.login()
        response = self.client.get(reverse("product-create_select"))
        self.assertEqual(response.status_code, 200)
        choices = [(self.ctype_id(model), model.__name__) for model in (Beans, Equipment, Subscription)]
        self.assertEqual(list(response.context["form"].fields["polymorphic_ctype_id"].choices), choices)
        for value, label in choices:
            self.assertContains(response, f'<option value="{value}">{label}</option>', html=True)
        self.assertContains(response, "Continue")
        self.assertContains(response, "col-md-4")
        beans = Beans.objects.first()
        response = self.client.get(reverse("product-detail", kwargs={"pk": beans.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [str(group.title) for group in response.context["object_detail_groups"]], ["Coffee", "Commerce", "About"]
        )
        self.assertContains(response, beans.name)
        self.assertContains(response, beans.sku)
        self.assertContains(response, beans.get_process_display())

    def test_card_list_shows_type_badges(self):
        self.login()
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        total = Product.objects.count()
        self.assertGreater(total, 12)  # the card list paginates by 12
        self.assertEqual(html.count('data-product-card="'), 12)
        for label in ("Beans", "Equipment", "Subscription"):
            self.assertIn(label, html)
        page_two = self.client.get(reverse("product-list"), {"page": 2}).content.decode()
        self.assertEqual(page_two.count('data-product-card="'), min(12, total - 12))
        last = self.client.get(reverse("product-list"), {"page": -(-total // 12)}).content.decode()
        self.assertEqual(last.count('data-product-card="'), total - 12 * (-(-total // 12) - 1))

    def test_table_list_renders(self):
        self.login()
        response = self.client.get(reverse("product-table"))
        self.assertContains(response, Product.objects.first().name)

    def test_create_select_then_typed_form(self):
        self.login()
        response = self.client.post(reverse("product-create_select"), {"polymorphic_ctype_id": self.ctype_id(Beans)})
        self.assertRedirects(
            response,
            reverse("product-create", kwargs={"polymorphic_ctype_id": self.ctype_id(Beans)}),
            fetch_redirect_response=False,
        )
        beans_form = self.client.get(response.url).content.decode()
        self.assertIn('name="process"', beans_form)
        self.assertIn('name="flavor_notes"', beans_form)
        equipment_url = reverse("product-create", kwargs={"polymorphic_ctype_id": self.ctype_id(Equipment)})
        self.assertIn('name="warranty_months"', self.client.get(equipment_url).content.decode())
        subscription_url = reverse("product-create", kwargs={"polymorphic_ctype_id": self.ctype_id(Subscription)})
        self.assertIn('name="bags_per_delivery"', self.client.get(subscription_url).content.decode())

    def test_create_beans(self):
        self.login()
        origin = Beans.objects.first().origin
        url = reverse("product-create", kwargs={"polymorphic_ctype_id": self.ctype_id(Beans)})
        response = self.client.post(
            url,
            {
                "name": "Test Lot",
                "slug": "test-lot",
                "sku": "T-1",
                "price": "12.50",
                "stock": "5",
                "is_active": "on",
                "origin": origin.pk,
                "process": "honey",
                "roast_level": "dark",
            },
        )
        self.assertEqual(response.status_code, 302, getattr(response, "context_data", None))
        self.assertEqual(Beans.objects.get(slug="test-lot").process, "honey")

    def test_detail_uses_object_detail_groups(self):
        self.login()
        beans = Beans.objects.first()
        html = self.client.get(reverse("product-detail", kwargs={"pk": beans.pk})).content.decode()
        for title in ("Coffee", "Commerce"):
            self.assertIn(title, html)
        self.assertRegex(html, rf">\s*{beans.get_process_display()}\s*<")

    def test_detail_of_each_type(self):
        """Each kind shows its own property labels and none of another kind's."""
        self.login()
        cases = (
            (Beans, "Altitude", ("Warranty months", "Bags per delivery")),
            (Equipment, "Warranty months", ("Altitude", "Bags per delivery")),
            (Subscription, "Bags per delivery", ("Altitude", "Warranty months")),
            (Beans, "Altitude", ("Warranty months", "Bags per delivery")),
        )
        original = deepcopy(PROPERTY_DISPLAY)
        for model, present, absent in cases:
            obj = model.objects.first()
            response = self.client.get(reverse("product-detail", kwargs={"pk": obj.pk}))
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn(present, html, model)
            self.assertIn("Commerce", html)
            self.assertIn("About", html)
            properties = {
                prop.path: prop.value for group in response.context["object_detail_groups"] for prop in group.properties
            }
            self.assertEqual(properties["sku"], obj.sku)
            field = {Beans: "altitude_m", Equipment: "warranty_months", Subscription: "bags_per_delivery"}[model]
            self.assertEqual(properties[field], getattr(obj, field))
            for label in absent:
                self.assertNotIn(label, html, model)
        self.assertIs(ProductDetailView.cv_property_display, PROPERTY_DISPLAY)
        self.assertEqual(PROPERTY_DISPLAY, original)

    def test_stock_row_only_for_stocked_kinds(self):
        """Subscriptions are not stocked (``show_stock = False``): their detail has no Stock row, like their card."""
        self.login()
        for model, shown in ((Beans, True), (Equipment, True), (Subscription, False)):
            html = self.client.get(reverse("product-detail", kwargs={"pk": model.objects.first().pk})).content.decode()
            with self.subTest(model=model.__name__):
                (self.assertRegex if shown else self.assertNotRegex)(html, r">\s*Stock\s*<")

    def test_update_and_delete_pages_render(self):
        self.login()
        for obj in (Beans.objects.first(), Equipment.objects.first(), Subscription.objects.first()):
            for name in ("product-update", "product-delete"):
                self.assertEqual(self.client.get(reverse(name, kwargs={"pk": obj.pk})).status_code, 200, name)

    def test_filters(self):
        self.login()
        count = Equipment.objects.count()
        response = self.client.get(reverse("product-list"), {"type": self.ctype_id(Equipment)})
        self.assertEqual(response.content.decode().count('data-product-card="'), count)

    def test_kim_cannot_edit_products(self):
        self.login("kim")
        product = Product.objects.first()
        self.assertEqual(self.client.get(reverse("product-update", kwargs={"pk": product.pk})).status_code, 403)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 200)

    def test_sam_can_view_not_create(self):
        self.login("sam")
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("product-create_select")).status_code, 403)

    def test_unprivileged_user_cannot_select_create_or_view_details(self):
        user = get_user_model().objects.create_user(username="no-catalog-permissions")
        self.client.force_login(user)
        selector = reverse("product-create_select")
        self.assertEqual(self.client.get(selector).status_code, 403)
        self.assertEqual(self.client.post(selector, {"polymorphic_ctype_id": self.ctype_id(Beans)}).status_code, 403)
        for model in (Beans, Equipment, Subscription):
            obj = model.objects.first()
            detail = reverse("product-detail", kwargs={"pk": obj.pk})
            create = reverse("product-create", kwargs={"polymorphic_ctype_id": self.ctype_id(model)})
            self.assertEqual(self.client.get(detail).status_code, 403)
            self.assertEqual(self.client.get(create).status_code, 403)
            self.assertEqual(self.client.post(create, {}).status_code, 403)


class ProductCardCssTests(SimpleTestCase):
    def test_product_card_title_keeps_its_tight_margin(self):
        css = (Path(__file__).resolve().parents[1] / "static" / "acme" / "acme.css").read_text()
        self.assertIn("[data-product-card] ~ .card-body .card-title { margin-bottom: .25rem; }", css)


class ProductMappingCheckTests(SimpleTestCase):
    def messages(self):
        return [message for check in ProductDetailView.checks() for message in check.messages()]

    def test_declared_mapping_checks(self):
        self.assertIs(ProductDetailView.cv_property_display, PROPERTY_DISPLAY)
        self.assertEqual(set(PROPERTY_DISPLAY), {Beans, Equipment, Subscription})
        self.assertEqual(self.messages(), [])

    def test_non_first_entry_diagnostics(self):
        original = deepcopy(PROPERTY_DISPLAY)
        for model in (Equipment, Subscription):
            with self.subTest(model=model.__name__, invalid="value"):
                mapping = {**PROPERTY_DISPLAY, model: None}
                with patch.object(ProductDetailView, "cv_property_display", mapping):
                    messages = self.messages()
                self.assertEqual([message.id for message in messages], ["viewset.E241"])
                self.assertIn(f"cv_property_display[{model._meta.label}]", messages[0].msg)
            with self.subTest(model=model.__name__, invalid="property"):
                mapping = deepcopy(PROPERTY_DISPLAY)
                mapping[model][0]["properties"][0] = 42
                with patch.object(ProductDetailView, "cv_property_display", mapping):
                    messages = self.messages()
                self.assertEqual([message.id for message in messages], ["viewset.E245"])
                self.assertIn(f"cv_property_display[{model._meta.label}][0]['properties'][0]", messages[0].msg)
            self.assertIs(ProductDetailView.cv_property_display, PROPERTY_DISPLAY)
            self.assertEqual(self.messages(), [])
        self.assertEqual(PROPERTY_DISPLAY, original)


class CategoryViewTests(CatalogTestCase):
    def test_category_up_down(self):
        self.login()
        first, second = Category.objects.all()[:2]
        self.assertEqual(self.client.post(reverse("category-down", kwargs={"pk": first.pk})).status_code, 302)
        self.assertEqual(list(Category.objects.all()[:2]), [second, first])
        self.client.post(reverse("category-up", kwargs={"pk": first.pk}))
        self.assertEqual(list(Category.objects.all()[:2]), [first, second])

    def test_category_pages_render(self):
        self.login()
        self.assertContains(self.client.get(reverse("category-list")), Category.objects.first().name)
        self.assertEqual(self.client.get(reverse("category-create")).status_code, 200)
