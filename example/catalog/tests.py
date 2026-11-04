import random

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from dashboard.seed import seed as seed_dashboard

from .models import Beans, Category, Equipment, Product, Subscription
from .seed import seed as seed_catalog


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
        response = self.client.post(
            reverse("product-create_select"), {"polymorphic_ctype_id": self.ctype_id(Beans)}
        )
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
                "name": "Test Lot", "slug": "test-lot", "sku": "T-1", "price": "12.50", "stock": "5",
                "is_active": "on", "origin": origin.pk, "process": "honey", "roast_level": "dark",
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
            (Equipment, "Warranty months", ("Altitude", "Bags per delivery")),
            (Subscription, "Bags per delivery", ("Altitude", "Warranty months")),
            (Beans, "Altitude", ("Warranty months", "Bags per delivery")),
        )
        for model, present, absent in cases:
            html = self.client.get(reverse("product-detail", kwargs={"pk": model.objects.first().pk})).content.decode()
            self.assertIn(present, html, model)
            self.assertIn("Commerce", html)
            for label in absent:
                self.assertNotIn(label, html, model)

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
