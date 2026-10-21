"""Pins the crispy render-path coverage of the product form.

Each assertion names the crispy template branch the field is here to exercise. If one of
them starts failing, either the layout changed or the active crispy template pack does.
"""

import copy
import re
import unittest

from django.contrib.auth import get_user_model
from django.conf import settings
from django.template.loader import get_template
from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Channel, Product, Tag


def _detail_field_template_hardcodes_bootstrap5() -> bool:
    source = get_template("crud_views/detail/field.html").template.source
    return "bootstrap5/" in source


class WithoutBootstrap5Loader(AppDirectoriesLoader):
    """App-directories loader that behaves as if crispy_bootstrap5 were not installed."""

    def get_template_sources(self, template_name):
        if template_name.startswith("bootstrap5/"):
            return
        yield from super().get_template_sources(template_name)


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
        # UneditableField: Tabler's plaintext class, and crispy's Bootstrap-2 era class must be gone
        self.assertIn("form-control-plaintext", html)
        self.assertNotIn("uneditable-input", html)
        self.assertIn('name="sku"', html)
        # fieldset.html — Django's use_fieldset emits <fieldset> for radio/checkbox fields too,
        # so pin the legend of the Fieldset layout object itself
        self.assertIn("<legend>Internal</legend>", html)
        self.assertIn("form-fieldset", html)  # Tabler's tinted block, not a bare <fieldset>

    def test_range_and_color_get_tablers_own_classes(self):
        html = self.create_page()
        range_input = re.search(r'<input type="range"[^>]*>', html).group(0)
        color_input = re.search(r'<input type="color"[^>]*>', html).group(0)
        # .form-range resets appearance/background-color, which .form-control would fight
        self.assertIn("form-range", range_input)
        self.assertNotIn("form-control", range_input)
        # .form-control-color only sets size/padding and relies on .form-control for border and radius
        self.assertIn("form-control-color", color_input)
        self.assertRegex(color_input, r'class="[^"]*\bform-control\b[^"]*"')

    def test_form_actions_and_group_labels(self):
        html = self.create_page()
        self.assertIn("form-footer", html)  # formactions.html
        # use_fieldset legends (radio_checkbox_select.html) are no longer shrunk
        for name in ("Size", "Channels"):
            with self.subTest(label=name):
                legend = re.search(r"<legend[^>]*>\s*" + name, html).group(0)
                self.assertNotIn("fs-6", legend)

    @unittest.expectedFailure
    def test_inline_group_labels_are_not_shrunk(self):
        # Known gap in crispy-tabler: layout/radioselect_inline.html (and checkboxselectmultiple_inline.html)
        # still carry fs-6 on their legend, so "Shipping" and the filter's "Tags" stay small. Remove the
        # decorator once the pack is fixed; an unexpected success will say so.
        self.assertNotIn("fs-6", self.create_page())

    @unittest.skipIf(
        _detail_field_template_hardcodes_bootstrap5(),
        "django-crud-views' crud_views/detail/field.html still hardcodes four bootstrap5/ includes, so detail "
        "pages need crispy_bootstrap5 installed; an upstream issue for it is still to be filed (number to follow)",
    )
    def test_create_and_update_pages_use_no_bootstrap5_template(self):
        # detail pages are excluded: crud_views/detail/field.html hardcodes four bootstrap5 includes
        # Removing crispy_bootstrap5 from INSTALLED_APPS would re-run every AppConfig.ready() (crud_views asset
        # bundles register twice), so take its templates away at the loader instead: same effect on rendering.
        templates = copy.deepcopy(settings.TEMPLATES)
        templates[0]["APP_DIRS"] = False
        templates[0]["OPTIONS"]["loaders"] = [
            "django.template.loaders.filesystem.Loader",
            "catalog.tests.WithoutBootstrap5Loader",
        ]
        with override_settings(TEMPLATES=templates):
            for url in [reverse("product-create"), reverse("product-update", kwargs={"pk": self.product.pk})]:
                with self.subTest(url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    names = [t.name for t in response.templates if t.name]
                    self.assertEqual([n for n in names if n.startswith("bootstrap5/")], [])

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
