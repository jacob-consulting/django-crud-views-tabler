from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from crud_views_tabler.icons import render_icon
from customers.models import Customer


class IconTests(SimpleTestCase):
    def test_tabler_name(self):
        svg = render_icon("eye", "icon-sm")
        self.assertIn('class="icon icon-sm"', svg)
        self.assertIn("<path", svg)

    def test_font_awesome_class_is_mapped(self):
        self.assertEqual(render_icon("fa-regular fa-trash-can"), render_icon("trash"))

    def test_unknown_icon_falls_back_to_the_class(self):
        self.assertEqual(render_icon("bi bi-star"), '<i class="bi bi-star" aria-hidden="true"></i>')

    def test_no_icon(self):
        self.assertEqual(render_icon(None), "")


class ThemeRenderingTests(TestCase):
    """Renders the demo customers ViewSet through the theme's templates."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("root", "root@example.com", "s3cret-pass")
        Customer.objects.bulk_create(Customer(name=f"Customer {i:02}", revenue=i) for i in range(15))
        cls.customer = Customer.objects.get(name="Customer 03")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_system_checks_pass(self):
        call_command("check", "--fail-level", "WARNING")

    def test_list_uses_tabler_table_and_icons(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn("table table-vcenter card-table", html)
        self.assertIn('class="table-sort"', html)
        self.assertIn("Showing 1–10 of 15", html)
        self.assertIn('cv-key="delete"', html)
        self.assertIn("btn-ghost-danger", html)
        self.assertNotIn("fa-regular", html)  # every Font Awesome default was mapped to a Tabler SVG

    def test_sorted_column_is_marked(self):
        html = self.client.get(reverse("customer-list"), {"sort": "-revenue"}).content.decode()
        self.assertIn('aria-sort="descending"', html)
        self.assertIn('class="table-sort desc"', html)
        self.assertLess(html.index("Customer 14"), html.index("Customer 13"))

    def test_scripts_load_jquery_and_shim_deferred(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        jquery = html.index("jquery-3.7.1.min.js")
        shim = html.index("crud_views_tabler/bootstrap-shim.js")
        core = html.index("crud_views/js/modal.js")
        self.assertLess(jquery, shim)
        self.assertLess(shim, core)
        self.assertNotIn('type="application/javascript"', html)

    def test_form_page_wraps_form_in_card(self):
        html = self.client.get(reverse("customer-create")).content.decode()
        self.assertIn('<div class="card"><div class="card-body">', html)
        self.assertIn('class="cv-form"', html)

    def test_delete_modal_partial_has_no_card_and_a_danger_button(self):
        url = reverse("customer-delete", args=[self.customer.pk])
        html = self.client.get(url, headers={"X-CV-Modal": "true"}).content.decode()
        self.assertIn('class="modal-header"', html)
        self.assertNotIn('<div class="card">', html)
        self.assertIn("btn btn-danger", html)

    def test_delete(self):
        url = reverse("customer-delete", args=[self.customer.pk])
        response = self.client.post(url, {"confirm": "on", "delete": "Delete"}, follow=True)
        self.assertContains(response, "Deleted »Customer 03«")
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_invalid_form_shows_tabler_validation(self):
        response = self.client.post(reverse("customer-create"), {"email": "nope", "status": "lead", "revenue": "0"})
        self.assertContains(response, "is-invalid")
        self.assertContains(response, "invalid-feedback")
