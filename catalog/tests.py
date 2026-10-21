"""Pins the crispy render-path coverage of the product form.

Each assertion names the crispy template branch the field is here to exercise. If one of
them starts failing, either the layout changed or the active crispy template pack does.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Product, Tag


class ProductFormCoverageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("root", "root@example.com", "s3cret-pass")
        cls.category = Category.objects.create(name="Audio")
        cls.tag = Tag.objects.create(name="new")
        cls.channel = Channel.objects.create(name="Online shop")
        cls.product = Product.objects.create(name="Studio Speaker", slug="studio-speaker", category=cls.category)

    def setUp(self):
        self.client.force_login(self.admin)

    def create_page(self) -> str:
        response = self.client.get(reverse("product-create"))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_list_detail_update_and_filter_render(self):
        for url in [
            reverse("product-list"),
            reverse("product-detail", kwargs={"pk": self.product.pk}),
            reverse("product-update", kwargs={"pk": self.product.pk}),
            reverse("product-delete", kwargs={"pk": self.product.pk}),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_filter_form_covers_checkbox_and_boolean_widgets(self):
        html = self.client.get(reverse("product-list"), {"cv_filter": "1"}).content.decode()
        self.assertIn('name="tags"', html)  # checkboxselectmultiple_inline.html
        self.assertIn('name="is_featured"', html)  # NullBooleanSelect
        self.assertIn('name="price_min"', html)

    def test_text_select_and_textarea_paths(self):
        html = self.create_page()
        # crispy prefixes the widget class name, so the class attribute is e.g. "textinput form-control"
        self.assertIn("form-control", html)  # field.html, text input
        self.assertIn("form-select", html)  # field.html, is_select
        self.assertIn("<textarea", html)
        self.assertIn('class="form-label requiredField"', html)  # required marker
        self.assertIn('class="asteriskField"', html)

    def test_help_text_and_file_paths(self):
        html = self.create_page()
        self.assertIn('class="form-text"', html)  # help_text.html
        self.assertIn('type="file"', html)  # field_file.html

    def test_checkbox_radio_and_switch_paths(self):
        html = self.create_page()
        self.assertIn("form-check-input", html)  # field.html, is_checkbox
        self.assertIn("form-check form-switch", html)  # switch.html
        self.assertIn('type="radio"', html)  # radio_checkbox_select.html
        self.assertIn("form-check-inline", html)  # radioselect_inline.html
        # InlineRadios over a Select widget renders <input type="select">; it needs RadioSelect
        self.assertNotIn('type="select"', html)

    def test_input_group_floating_and_uneditable_paths(self):
        html = self.create_page()
        self.assertIn('class="input-group"', html)  # prepended_appended_text.html
        self.assertIn('class="input-group-text">€</span>', html)
        self.assertIn("months</span>", html)
        self.assertIn("form-floating", html)  # floating_field.html
        # uneditable_input.html: crispy's own Bootstrap-2 era class, and no form-control at all
        self.assertIn("uneditable-input", html)
        self.assertIn('name="sku"', html)
        # fieldset.html — Django's use_fieldset emits <fieldset> for radio/checkbox fields too,
        # so pin the legend of the Fieldset layout object itself
        self.assertIn("<legend>Internal</legend>", html)

    def test_native_input_types_reach_the_browser(self):
        html = self.create_page()
        for input_type in ["date", "datetime-local", "time", "color", "range"]:
            with self.subTest(input_type=input_type):
                self.assertIn(f'type="{input_type}"', html)

    def test_the_generated_sku_survives_a_create(self):
        html = self.create_page()
        self.assertIn("SKU-", html)
        response = self.client.post(
            reverse("product-create"),
            {
                "name": "Rugged Hub", "slug": "rugged-hub", "description": "",
                "category": self.category.pk, "tags": [self.tag.pk], "channels": [self.channel.pk],
                "size": Product.Size.M, "shipping": Product.Shipping.STANDARD,
                "price": "19.90", "warranty_months": 24, "stock": 5, "rating": 4,
                "released_on": "", "published_at": "", "restock_at": "",
                "is_active": "on", "accent_color": "#066fd1",
                "contact_email": "", "website": "", "internal_notes": "",
                "submit": "Save",
            },
        )
        # MessageMixin renders the message template, so response.context is not the form's context
        self.assertEqual(response.status_code, 302, response.content[:400])
        product = Product.objects.get(slug="rugged-hub")
        self.assertTrue(product.sku.startswith("SKU-"))
        self.assertEqual(list(product.tags.all()), [self.tag])
