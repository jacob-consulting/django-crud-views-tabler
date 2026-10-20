import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.checks import run_checks
from django.core.management import call_command
from django.template.loader import get_template
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES, get_button_classes
from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.icons import DEFAULT_ICONS
from crud_views.lib.icons import render_icon as cv_render_icon
from crud_views_tabler.buttons import TABLER_BUTTON_CLASSES
from crud_views_tabler.icons import ICONS, TABLER_ICONS, render, svg
from customers.models import Customer
from customers.views import CustomerDeleteView, CustomerListView


class TablerIconTests(SimpleTestCase):
    def test_svg_for_a_tabler_name(self):
        html = svg("eye", "icon-sm")
        self.assertIn('class="icon icon-sm"', html)
        self.assertIn("<path", html)
        self.assertIn('aria-hidden="true"', html)

    def test_svg_without_extra_classes_has_no_trailing_space(self):
        self.assertIn('class="icon"', svg("eye"))

    def test_unknown_or_empty_name_renders_nothing(self):
        self.assertEqual(svg("not-an-icon"), "")
        self.assertEqual(svg(None), "")
        self.assertEqual(render("not-an-icon", css="", config={}), "")

    def test_css_is_escaped(self):
        self.assertIn('class="icon a&quot; onload=&quot;x"', svg("eye", 'a" onload="x'))

    def test_renderer_matches_svg(self):
        self.assertEqual(render("trash", css="icon-sm", config={"renderer": "x"}), svg("trash", "icon-sm"))

    def test_every_upstream_icon_name_is_mapped(self):
        self.assertEqual(set(TABLER_ICONS), set(DEFAULT_ICONS))
        for name, value in TABLER_ICONS.items():
            prefix, tabler_name = value.split(":", 1)
            self.assertEqual(prefix, "tabler", name)
            self.assertIn(tabler_name, ICONS, f"{name} -> {value} has no path in ICONS")

    def test_registry_renders_tabler_svg(self):
        self.assertEqual(cv_render_icon("detail"), svg("eye"))
        self.assertEqual(cv_render_icon("tabler:building-store", css="icon-sm"), svg("building-store", "icon-sm"))

    @override_settings(CRUD_VIEWS_ICONS={"detail": "far:eye"})
    def test_project_setting_wins_over_the_theme(self):
        self.assertEqual(cv_render_icon("detail"), '<i class="fa-regular fa-eye" aria-hidden="true"></i>')


class ButtonClassTests(SimpleTestCase):
    def test_theme_classes_are_registered(self):
        resolved = get_button_classes()
        for key, classes in TABLER_BUTTON_CLASSES.items():
            self.assertEqual(resolved[key], classes, key)

    def test_every_theme_key_is_an_upstream_key(self):
        self.assertLessEqual(set(TABLER_BUTTON_CLASSES), set(DEFAULT_BUTTON_CLASSES))

    def test_table_values(self):
        expected = {
            "context:primary": "btn btn-primary btn-icon",
            "context:secondary": "btn btn-icon",
            "context:tertiary": "btn btn-icon",
            "context:danger": "btn btn-icon btn-outline-danger",
            "list:primary": "btn btn-sm btn-icon btn-ghost-primary",
            "list:secondary": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:tertiary": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:danger": "btn btn-sm btn-icon btn-ghost-danger",
            "card:primary": "btn btn-sm btn-primary",
            "card:secondary": "btn btn-sm",
            "card:tertiary": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:danger": "btn btn-sm btn-ghost-danger",
            "context:container": "btn-list",
            "list:container": "btn-list flex-nowrap justify-content-end gap-1",
            "card:container": "btn-list",
            "context:menu-toggle": "btn btn-icon",
            "list:menu-toggle": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:menu-toggle": "btn btn-sm btn-icon",
            "context:menu-wrapper": "dropdown",
            "list:menu-wrapper": "dropdown",
            "form:delete": "btn btn-danger",
            "card-order:toggle": "btn btn-icon",
            "card-order:container": "btn-group",
            "formset:control": "btn btn-icon",
            "formset:control-danger": "btn btn-icon btn-danger",
        }
        self.assertEqual(TABLER_BUTTON_CLASSES, expected)

    @override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:danger": "x-danger"})
    def test_project_setting_wins_over_the_theme_classes(self):
        self.assertEqual(get_button_classes()["list:danger"], "x-danger")


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
        self.assertNotIn("fa-regular", html)
        self.assertNotIn("fa-solid", html)
        self.assertNotIn("<i class=", html)  # every icon on the page is a Tabler SVG
        self.assertIn(svg("building-store"), html)  # the ViewSet header icon, tabler:building-store

    def test_disabled_action_renders_a_tabler_icon(self):
        viewer = get_user_model().objects.create_user("viewer", password="viewer-pass")
        viewer.user_permissions.add(Permission.objects.get(codename="view_customer", content_type__app_label="customers"))
        self.client.force_login(viewer)
        with mock.patch.object(CustomerDeleteView, "cv_inaccessible_actions", "disable"):
            html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*data-cv-disabled="permission"[^>]*>.*?</button>', html, re.S)
        self.assertIsNotNone(button)
        self.assertIn("<svg", button.group(0))
        self.assertNotIn("<i class=", button.group(0))

    def test_dashboard_icons_still_render(self):
        html = self.client.get("/").content.decode()
        self.assertIn("<svg", html)
        self.assertNotIn("<i class=", html)

    def test_sorted_column_is_marked(self):
        html = self.client.get(reverse("customer-list"), {"sort": "-revenue"}).content.decode()
        self.assertIn('aria-sort="descending"', html)
        self.assertIn('class="table-sort desc"', html)
        self.assertLess(html.index("Customer 14"), html.index("Customer 13"))

    def test_scripts_use_the_tabler_adapter_without_jquery(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertNotIn("jquery", html.lower())
        self.assertNotIn("bootstrap-shim", html)
        core = html.index("crud_views/js/adapters.js")
        theme = html.index("crud_views_tabler/tabler-adapters.js")
        self.assertLess(core, theme)
        self.assertIn("crud_views/js/modal.js", html)

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
        self.assertIn("data-cv-modal-dismiss", html)
        self.assertNotIn("data-bs-dismiss", html)

    def test_delete_form_is_the_stock_crispy_delete_form(self):
        self.assertIs(CustomerDeleteView.form_class, CrispyDeleteForm)
        html = self.client.get(reverse("customer-delete", args=[self.customer.pk])).content.decode()
        self.assertRegex(html, r'<input type="submit"[^>]*class="btn btn-danger"')
        self.assertNotIn("btn-primary btn-danger", html)

    def test_delete(self):
        url = reverse("customer-delete", args=[self.customer.pk])
        response = self.client.post(url, {"confirm": "on", "delete": "Delete"}, follow=True)
        self.assertContains(response, "Deleted »Customer 03«")
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_invalid_form_shows_tabler_validation(self):
        response = self.client.post(reverse("customer-create"), {"email": "nope", "status": "lead", "revenue": "0"})
        self.assertContains(response, "is-invalid")
        self.assertContains(response, "invalid-feedback")

    def test_modal_shell_is_tabler(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('class="modal modal-blur fade" id="cv-modal"', html)
        self.assertIn('class="modal-dialog modal-dialog-centered" id="cv-modal-dialog"', html)
        self.assertIn('id="cv-modal-content"', html)

    def test_filter_toggle_contract(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*id="cv-filter-toggle"[^>]*>.*?</button>', html, re.S).group(0)
        self.assertIn('aria-controls="filter-collapse"', button)
        self.assertIn('aria-expanded="false"', button)
        self.assertIn("data-cv-tooltip", button)
        self.assertIn('<span data-cv-filter-icon="open">', button)
        self.assertIn('<span data-cv-filter-icon="close" class="d-none">', button)
        self.assertEqual(button.count("<svg"), 2)

    def test_filter_toggle_reflects_the_session_state(self):
        response = self.client.post(
            reverse("customer-list"), data='{"filter_expanded": true}', content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*id="cv-filter-toggle"[^>]*>.*?</button>', html, re.S).group(0)
        self.assertIn('aria-expanded="true"', button)
        self.assertIn('<span data-cv-filter-icon="open" class="d-none">', button)
        self.assertIn('<span data-cv-filter-icon="close">', button)
        self.assertIn('class="collapse show" id="filter-collapse"', html)

    def test_pinned_filter_has_no_toggle(self):
        with mock.patch.object(CustomerListView, "cv_filter_pinned", True):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('id="filter-pinned"', html)
        self.assertNotIn('id="cv-filter-toggle"', html)
        self.assertIn("<svg", html[html.index('id="filter-pinned"'):][:800])  # the card header's filter icon

    def test_action_tooltips_are_initialised_by_crud_views(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        buttons = re.findall(r"<(?:a|button)\b[^>]*\bcv-key=[^>]*>", html)
        self.assertGreater(len(buttons), 3)
        for tag in buttons:
            self.assertNotIn('data-bs-toggle="tooltip"', tag)
        self.assertTrue(any("data-cv-tooltip" in tag for tag in buttons))

    def test_near_copies_of_upstream_templates_are_not_overridden(self):
        # Their only differences were spacing or markup Tabler does not need; the theme styles crud_views' version.
        for name in ("crud_views/modal/content.html", "crud_views/tags/actions_menu_item_label.html",
                     "crud_views/tags/breadcrumb.html"):
            self.assertNotIn("crud_views_tabler", get_template(name).origin.name, name)

    def test_menu_items_use_the_fixed_width_icon_slot(self):
        with mock.patch.object(CustomerListView, "cv_list_actions_inline", ["detail"]):
            html = self.client.get(reverse("customer-list")).content.decode()
        item = re.search(r'<a\b[^>]*class="dropdown-item[^"]*"[^>]*cv-key="update"[^>]*>.*?</a>', html, re.S).group(0)
        self.assertIn('class="icon cv-icon-fw"', item)

    def test_breadcrumb_is_a_nav_landmark(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('<nav aria-label="breadcrumb">', html)


class CardThemeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("root", "root@example.com", "s3cret-pass")
        Customer.objects.bulk_create(Customer(name=f"Customer {i:02}", revenue=i * 10) for i in range(15))

    def setUp(self):
        self.client.force_login(self.admin)

    def get(self, **params):
        return self.client.get(reverse("customer-card"), params).content.decode()

    def test_cards_render_in_tabler_grid(self):
        html = self.get()
        self.assertIn('class="row row-deck row-cards"', html)
        self.assertEqual(html.count('class="card-footer"'), 12)  # paginate_by
        self.assertIn('class="pagination', html)
        self.assertNotIn("fa-solid", html)
        self.assertNotIn("<i class=", html)

    def test_card_action_variants(self):
        html = self.get()
        self.assertIn("btn btn-sm btn-primary flex-grow-1", html)  # primary + flex
        self.assertIn("btn btn-sm btn-ghost-secondary btn-icon", html)  # tertiary + no_label
        self.assertIn('<span class="visually-hidden">Delete</span>', html)  # icon-only keeps a name

    def test_card_links_carry_their_origin(self):
        html = self.get()
        self.assertIn("/update/?cv_from=card", html)
        self.assertIn("/delete/?cv_from=card", html)

    def test_order_bar(self):
        html = self.get(order="revenue", dir="desc")
        self.assertIn('id="cv-card-order-form"', html)
        self.assertIn('value="desc" class="btn btn-icon active"', html)
        self.assertRegex(html, r'<button[^>]*value="asc"[^>]*>\s*<svg')
        self.assertLess(html.index("Customer 14"), html.index("Customer 13"))

    def test_empty_state(self):
        html = self.get(name="nothing-matches", submit="Apply Filter")
        self.assertIn('class="empty"', html)
        self.assertIn("No items found.", html)

    def test_delete_from_card_returns_to_cards(self):
        customer = Customer.objects.get(name="Customer 03")
        url = reverse("customer-delete", args=[customer.pk]) + "?cv_from=card"
        response = self.client.post(url, {"confirm": "on", "delete": "Delete"})
        self.assertRedirects(response, reverse("customer-card"), fetch_redirect_response=False)

    def test_icon_only_card_action_has_a_crud_views_tooltip(self):
        html = self.get()
        delete = re.search(r'<a\b[^>]*/delete/\?cv_from=card[^>]*>', html).group(0)  # the no_label card action
        self.assertIn("btn-icon", delete)
        self.assertIn("data-cv-tooltip", delete)
        self.assertNotIn('data-bs-toggle="tooltip"', delete)


class IconCheckTests(SimpleTestCase):
    @override_settings(CRUD_VIEWS_ICONS={"detail": "tabler:does-not-exist"})
    def test_unknown_tabler_icon_is_reported(self):
        messages = [m for m in run_checks() if m.id == "crud_views_tabler.W001"]
        self.assertEqual(len(messages), 1)
        self.assertIn("'detail'", messages[0].msg)
        self.assertIn("'tabler:does-not-exist'", messages[0].msg)

    @override_settings(CRUD_VIEWS_ICONS={"detail": "far:eye", "person": "tabler:user"})
    def test_other_library_values_are_not_reported(self):
        self.assertEqual([m.id for m in run_checks() if m.id.startswith("crud_views_tabler.")], [])

    @override_settings(
        CRUD_VIEWS_ICONS={"detail": "tabler:does-not-exist"},
        CRUD_VIEWS_ICON_LIBRARIES={"tabler": {"renderer": "font", "class": "ti ti-{name}"}},
    )
    def test_remapped_tabler_library_is_not_reported(self):
        self.assertEqual([m.id for m in run_checks() if m.id.startswith("crud_views_tabler.")], [])

    @override_settings(CRUD_VIEWS_ICONS={"detail": " tabler:nope "})
    def test_value_with_surrounding_whitespace_is_reported(self):
        messages = [m for m in run_checks() if m.id == "crud_views_tabler.W001"]
        self.assertEqual(len(messages), 1)
        self.assertIn("'nope'", messages[0].msg)
