import re
from unittest import mock

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.core.checks import run_checks
from django.core.management import call_command
from django.template import Context, Template, TemplateDoesNotExist
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES, get_button_classes
from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.icons import DEFAULT_ICONS
from crud_views.lib.icons import render_icon as cv_render_icon
from crud_views.lib.view.label_mode import LABEL_MODES
from crud_views.lib.view.variant import VARIANTS
from crud_views_tabler.buttons import TABLER_BUTTON_CLASSES
from crud_views_tabler.icons import TABLER_ICONS, render
from customers.models import Customer
from customers.views import CustomerDeleteView, CustomerListView
from django_tabler.icons import ICONS, svg


class ProbeWidget(forms.TextInput):
    class Media:
        js = ("probe/probe.js",)
        css = {"all": ("probe/probe.css",)}


class ProbeForm(forms.Form):
    x = forms.CharField(widget=ProbeWidget)


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
        # A label-mode key (location:variant:mode, #209) extends an upstream action key.
        for key in TABLER_BUTTON_CLASSES:
            base, _, mode = key.rpartition(":") if key.count(":") == 2 else (key, "", "")
            self.assertIn(base, DEFAULT_BUTTON_CLASSES, key)
            if mode:
                self.assertIn(mode, LABEL_MODES, key)

    def test_btn_icon_only_on_icon_only_buttons(self):
        # btn-icon squares a button; a labelled button (label or both) must not get it.
        for key, classes in TABLER_BUTTON_CLASSES.items():
            if key.split(":")[0] in ("context", "list", "card") and key.split(":")[1] in VARIANTS:
                self.assertEqual("btn-icon" in classes.split(), key.endswith(":icon"), key)

    def test_table_values(self):
        expected = {
            "context:primary": "btn btn-primary",
            "context:secondary": "btn",
            "context:tertiary": "btn",
            "context:danger": "btn btn-outline-danger",
            "list:primary": "btn btn-sm btn-ghost-primary",
            "list:secondary": "btn btn-sm btn-ghost-secondary",
            "list:tertiary": "btn btn-sm btn-ghost-secondary",
            "list:danger": "btn btn-sm btn-ghost-danger",
            "card:primary": "btn btn-sm btn-primary",
            "card:secondary": "btn btn-sm",
            "card:tertiary": "btn btn-sm btn-ghost-secondary",
            "card:danger": "btn btn-sm btn-ghost-danger",
            "context:primary:icon": "btn btn-primary btn-icon",
            "context:secondary:icon": "btn btn-icon",
            "context:tertiary:icon": "btn btn-icon",
            "context:danger:icon": "btn btn-icon btn-outline-danger",
            "list:primary:icon": "btn btn-sm btn-icon btn-ghost-primary",
            "list:secondary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:tertiary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:danger:icon": "btn btn-sm btn-icon btn-ghost-danger",
            "card:primary:icon": "btn btn-sm btn-icon btn-primary",
            "card:secondary:icon": "btn btn-sm btn-icon",
            "card:tertiary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:danger:icon": "btn btn-sm btn-icon btn-ghost-danger",
            "context:container": "btn-list",
            "list:container": "btn-list flex-nowrap justify-content-end gap-1",
            "card:container": "btn-list",
            "context:menu-toggle": "btn btn-icon",
            "list:menu-toggle": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:menu-toggle": "btn btn-sm btn-icon",
            "card:root": "card",
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

    @staticmethod
    def tag(html, key):
        """The first opening <a> or <button> tag with cv-key=key."""
        return re.search(rf'<(?:a|button)\b[^>]*\bcv-key="{key}"[^>]*>', html).group(0)

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

    def test_table_pagination_uses_the_semantic_arrows(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        footer = html[html.index('class="pagination'):]
        self.assertIn(str(svg("chevron-right")), footer[:2000])
        with override_settings(CRUD_VIEWS_ICONS={"page-next": "tabler:arrow-left"}):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn(str(svg("arrow-left")), html[html.index('class="pagination'):][:2000])

    def test_disabled_action_renders_a_tabler_icon(self):
        viewer = get_user_model().objects.create_user("viewer", password="viewer-pass")
        viewer.user_permissions.add(Permission.objects.get(codename="view_customer", content_type__app_label="customers"))
        self.client.force_login(viewer)
        with mock.patch.object(CustomerDeleteView, "cv_inaccessible_actions", "disable"):
            html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*data-cv-disabled="permission"[^>]*>.*?</button>', html, re.S)
        self.assertIsNotNone(button)
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-danger"', button.group(0))
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

    def test_tooltip_adapter_places_toolbar_tooltips_below(self):
        from django.contrib.staticfiles import finders
        with open(finders.find("crud_views_tabler/tabler-adapters.js"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("cv.bootstrapAdapters(() => globalThis.tabler)", source)
        self.assertIn("cv.adapters.tooltip.init", source)
        self.assertIn('location === "context"', source)
        self.assertIn('"bottom"', source)
        self.assertIn("globalThis.tabler?.Tooltip", source)

    def test_tooltip_adapter_keeps_upstream_lifecycle(self):
        # Only init is replaced, so crud_views' hide(el) / dispose(el) (#205) keep resolving tabler.Tooltip.
        from django.contrib.staticfiles import finders
        with open(finders.find("crud_views_tabler/tabler-adapters.js"), encoding="utf-8") as f:
            source = f.read()
        self.assertNotRegex(source, r"cv\.adapters\.tooltip\s*=")
        self.assertNotIn("cv.adapters.tooltip.hide", source)
        self.assertNotIn("cv.adapters.tooltip.dispose", source)
        with open(finders.find("crud_views/js/adapters.js"), encoding="utf-8") as f:
            core = f.read()
        self.assertIn("hide(el)", core)
        self.assertIn("dispose(el)", core)

    def test_form_page_wraps_form_in_card(self):
        html = self.client.get(reverse("customer-create")).content.decode()
        self.assertIn('<div class="card"><div class="card-body">', html)
        self.assertIn('class="cv-form"', html)

    def test_modal_form_has_no_card(self):
        html = self.client.get(reverse("customer-create"), headers={"X-CV-Modal": "true"}).content.decode()
        self.assertIn('class="cv-form"', html)
        self.assertNotIn('<div class="card">', html)

    def test_form_pages_frame_through_upstream_content_templates(self):
        # upstream #239: the theme overrides only the frame, not the form templates
        self.assertIn("crud_views_tabler", get_template("crud_views/snippets/form_frame.html").origin.name)
        for name in ("view_create", "view_update", "view_delete", "view_custom_form"):
            template = f"crud_views/{name}.content.html"
            self.assertNotIn("crud_views_tabler", get_template(template).origin.name, template)

    def test_alerts_go_through_the_theme_frame_only(self):
        # upstream #250: every alert renders through tags/alert.html; the theme overrides that frame and nothing else
        self.assertIn("crud_views_tabler", get_template("crud_views/tags/alert.html").origin.name)
        for name in ("tags/messages.html", "snippets/delete/protection_errors.html",
                     "snippets/delete/related_objects.html", "snippets/alert/text.html", "snippets/alert/list.html"):
            self.assertNotIn("crud_views_tabler", get_template(f"crud_views/{name}").origin.name, name)

    def test_protection_errors_render_as_tabler_alert(self):
        html = render_to_string(
            "crud_views/snippets/delete/protection_errors.html", {"delete_protection_errors": ["Has open orders"]}
        )
        self.assertIn('class="alert alert-danger"', html)
        self.assertIn(f'<div class="alert-icon">{svg("alert-circle", "alert-icon")}</div>', html)
        self.assertIn('<h4 class="alert-heading">This object cannot be deleted:</h4>', html)
        self.assertRegex(html, r'<div class="alert-description">\s*<ul[^>]*>\s*<li>Has open orders</li>')
        self.assertNotIn("btn-close", html)

    def test_related_objects_alerts_get_the_tabler_layout(self):
        html = render_to_string(
            "crud_views/snippets/delete/related_objects.html",
            {"protected_objects": ["Order 7"], "related_summary": {"order": 2}, "related_summary_items": ["order: 2"],
             "related_objects": []},
        )
        self.assertEqual(html.count('<div class="alert-icon">'), 3)
        self.assertEqual(html.count('class="alert-heading"'), 3)
        self.assertIn(str(svg("alert-triangle", "alert-icon")), html)  # warning
        self.assertIn("<li>order: 2</li>", html)

    def test_create_and_update_post_multipart(self):
        # upstream #236: without the enctype a FileField arrives empty
        for url in (reverse("customer-create"), reverse("customer-update", args=[self.customer.pk])):
            html = self.client.get(url).content.decode()
            form = re.search(r'<form class="cv-form"[^>]*>', html).group(0)
            self.assertIn('enctype="multipart/form-data"', form, url)

    def test_create_and_update_emit_widget_media_once(self):
        # upstream #191: crispy already renders form.media; the content template must not add it again
        request = RequestFactory().get("/")
        for template in ("crud_views/view_create.content.html", "crud_views/view_update.content.html"):
            html = render_to_string(template, {"form": ProbeForm(), "request": request, "view": None}, request=request)
            self.assertEqual(html.count("probe/probe.js"), 1, template)
            self.assertEqual(html.count("probe/probe.css"), 1, template)

    def test_messages_render_as_tabler_alerts(self):
        url = reverse("customer-delete", args=[self.customer.pk])
        html = self.client.post(url, {"confirm": "on", "delete": "Delete"}, follow=True).content.decode()
        alert = re.search(r'<div class="alert alert-success[^"]*"[^>]*>.*?</div>\s*</div>', html, re.S).group(0)
        self.assertIn("alert-dismissible", alert)
        self.assertIn('<div class="alert-icon">', alert)
        self.assertIn(str(svg("check", "alert-icon")), alert)
        self.assertIn("<div>Deleted »Customer 03«", alert)  # no heading: the text sits in a plain div
        self.assertNotIn("alert-heading", alert)

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
        self.assertIn('class="btn btn-icon"', button)
        self.assertIn('data-cv-tooltip="context"', button)
        self.assertIn('<span data-cv-filter-icon="open">', button)
        self.assertIn('<span data-cv-filter-icon="close" hidden>', button)
        self.assertEqual(button.count("<svg"), 2)

    def test_filter_toggle_reflects_the_session_state(self):
        response = self.client.post(
            reverse("customer-list"), data='{"filter_expanded": true}', content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*id="cv-filter-toggle"[^>]*>.*?</button>', html, re.S).group(0)
        self.assertIn('aria-expanded="true"', button)
        self.assertIn('<span data-cv-filter-icon="open" hidden>', button)
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
        for key in ("list", "card", "create"):  # the filter toggle is checked by id in test_filter_toggle_contract
            self.assertIn('data-cv-tooltip="context"', self.tag(html, key), key)

    def test_toolbar_uses_theme_classes(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        create = self.tag(html, "create")
        self.assertIn('class="btn btn-primary btn-icon"', create)
        self.assertIn('data-cv-tooltip="context"', create)
        self.assertIn('class="btn btn-icon active"', self.tag(html, "list"))
        self.assertIn('aria-current="page"', self.tag(html, "list"))
        self.assertRegex(html, r'<fieldset class="btn-list" aria-label="Actions" cv-context-container="true">')

    def test_row_actions_use_theme_classes(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        delete = self.tag(html, "delete")
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-danger"', delete)
        self.assertIn('data-cv-tooltip="list"', delete)
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-secondary"', self.tag(html, "update"))
        self.assertIn('<fieldset class="btn-list flex-nowrap justify-content-end gap-1"', html)

    def test_overflow_menu_uses_theme_classes(self):
        with mock.patch.object(CustomerListView, "cv_list_actions_inline", ["detail"]):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('<div class="dropdown">', html)
        self.assertRegex(html, r'class="btn btn-sm btn-icon btn-ghost-secondary dropdown-toggle cv-menu-toggle"')

    def test_upstream_templates_are_not_overridden(self):
        # Near copies (spacing or markup Tabler does not need) and every template whose only job was button classes,
        # the primary action or the tooltip marker: the class table and crud_views' leaves cover those.
        for name in ("crud_views/modal/content.html", "crud_views/tags/actions_menu_item_label.html",
                     "crud_views/tags/breadcrumb.html", "crud_views/tags/context_action.html",
                     "crud_views/tags/list_action.html", "crud_views/tags/card_action.html",
                     "crud_views/tags/context_actions.html", "crud_views/columns/actions.html",
                     "crud_views/tags/actions_menu_toggle.html", "crud_views/tags/context_action_filter.html",
                     "crud_views/snippets/card_order.html"):
            self.assertNotIn("crud_views_tabler", get_template(name).origin.name, name)
        with self.assertRaises(TemplateDoesNotExist):
            get_template("crud_views/tags/list_action.inner.html")
        for name in ("crud_views/tags/button/action.html", "crud_views/tags/button/container.html",
                     "crud_views/tags/button/menu_item.html", "crud_views/tags/button/menu_item_label.html"):
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
        self.assertEqual(html.count('class="btn-list" cv-card-container="true"'), 12)
        self.assertIn('class="pagination', html)
        self.assertNotIn("fa-solid", html)
        self.assertNotIn("<i class=", html)

    def test_card_action_variants(self):
        html = self.get()
        self.assertIn('class="btn btn-sm btn-primary flex-grow-1"', html)  # primary + flex, labelled: no btn-icon
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-secondary"', html)  # tertiary:icon (the demo's delete)
        open_ = re.search(r'<a\b[^>]*cv-key="detail"[^>]*>.*?</a>', html, re.S).group(0)
        self.assertIn("<svg", open_)  # label mode "both", upstream's card default (#213): icon and text
        self.assertIn("<span>Open</span>", open_)
        self.assertIn('<span class="visually-hidden">Delete</span>', html)  # icon-only keeps a name

    def test_card_follows_upstream_block_names_and_class_keys(self):
        # upstream #243: same block names as crud_views' card, so a cv_card_template works under either theme
        template = Template(
            '{% extends "crud_views/tags/card.html" %}'
            "{% block card_title %}T{% endblock %}{% block card_content %}<p>C</p>{% endblock %}"
            "{% block card_actions %}{% endblock %}"
        )
        page = self.client.get(reverse("customer-card")).context
        customer = Customer.objects.get(name="Customer 03")
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:title": "card-title x-title"}):
            html = template.render(Context({"object": customer, "view": page["view"], "request": page["request"]}))
        self.assertIn('<div class="card">', html)  # card:root without mb-3: the row-deck grid spaces the cards
        self.assertIn('<h3 class="card-title x-title">T</h3>', html)
        self.assertIn("<p>C</p>", html)
        self.assertNotIn("card-footer", html)  # dropping the actions drops the footer with them
        self.assertNotIn("cv-card-container", html)

    def test_card_links_carry_their_origin(self):
        html = self.get()
        self.assertIn("/update/?cv_from=card", html)
        self.assertIn("/delete/?cv_from=card", html)

    def test_pagination_is_upstream_with_tabler_chevrons(self):
        # upstream #241: accessible markup and arrows from the icon registry; the theme maps the icons only
        self.assertNotIn("crud_views_tabler", get_template("crud_views/snippets/pagination.html").origin.name)
        html = self.get(page=2)
        nav = re.search(r'<nav aria-label="pagination".*?</nav>', html, re.S).group(0)
        self.assertIn(str(svg("chevron-left")), nav)
        self.assertIn(str(svg("chevron-right")), nav)
        self.assertIn('<li class="page-item active" aria-current="page">', nav)
        self.assertIn('<a class="page-link" aria-disabled="true">', nav)  # page 2 of 2: no next page
        self.assertIn('<span class="visually-hidden">previous</span>', nav)

    def test_order_bar(self):
        html = self.get(order="revenue", dir="desc")
        self.assertIn('id="cv-card-order-form"', html)
        self.assertRegex(html, r'value="desc"\s+class="btn btn-icon active"')
        self.assertIn('<fieldset class="btn-group"', html)
        self.assertRegex(html, r'<button[^>]*value="asc"[^>]*>\s*<svg')
        self.assertLess(html.index("Customer 14"), html.index("Customer 13"))

    def test_empty_state(self):
        html = self.get(name="nothing-matches", submit="Apply Filter")
        self.assertIn('class="empty"', html)
        self.assertIn("No items found.", html)

    @override_settings(LANGUAGE_CODE="de")
    def test_empty_state_is_translated(self):
        # the theme's empty state shares its msgid with crud_views' card list, translated upstream (#246)
        html = self.get(name="nothing-matches", submit="Apply Filter")
        self.assertIn('class="empty"', html)
        self.assertIn("Keine Einträge gefunden.", html)

    def test_delete_from_card_returns_to_cards(self):
        customer = Customer.objects.get(name="Customer 03")
        url = reverse("customer-delete", args=[customer.pk]) + "?cv_from=card"
        response = self.client.post(url, {"confirm": "on", "delete": "Delete"})
        self.assertRedirects(response, reverse("customer-card"), fetch_redirect_response=False)

    def test_icon_only_card_action_has_a_crud_views_tooltip(self):
        html = self.get()
        delete = re.search(r'<a\b[^>]*/delete/\?cv_from=card[^>]*>', html).group(0)  # the label_mode="icon" action
        self.assertIn("btn-icon", delete)
        self.assertIn('data-cv-tooltip="card"', delete)
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


class MessagesParityTests(SimpleTestCase):
    def test_plain_include_matches_cv_messages(self):
        messages = [
            Message(constants.DEBUG, "d"),
            Message(constants.INFO, "i"),
            Message(constants.SUCCESS, "s", extra_tags="probe"),
            Message(constants.WARNING, "<b>w</b>"),
            Message(constants.ERROR, "e"),
            Message(35, "custom"),
        ]

        def normalized(html):
            return re.sub(r">\s+<", "><", re.sub(r"\s+", " ", html)).strip()

        plain = render_to_string("django_tabler/includes/messages.html", {"messages": messages})
        themed = Template("{% load crud_views %}{% cv_messages %}").render(Context({"messages": messages}))
        self.assertEqual(normalized(plain), normalized(themed))
